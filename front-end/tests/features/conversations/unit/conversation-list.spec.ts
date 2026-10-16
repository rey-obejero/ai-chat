import { mount, type DOMWrapper, type VueWrapper } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import type { MenuItem } from 'primevue/menuitem'
import Tooltip from 'primevue/tooltip'
import { describe, expect, it } from 'vitest'
import { defineComponent, type PropType } from 'vue'

import type { Conversation } from '@/features/conversations/api'
import ConversationList from '@/features/conversations/components/ConversationList.vue'

/**
 * PrimeVue's popup teleports its items to the body, which a test cannot click
 * through meaningfully here; this stub renders the same items in place. That the
 * items are absent until the trigger is clicked is itself the assertion that the
 * row was handed to the menu — the model is empty until then.
 */
const MenuStub = defineComponent({
  name: 'MenuStub',
  props: {
    model: { type: Array as PropType<MenuItem[]>, default: () => [] },
  },
  expose: ['toggle'],
  methods: {
    toggle(): void {},
  },
  template: `<div class="menu-stub">
    <template v-for="(item, index) in model" :key="index">
      <hr v-if="item.separator" />
      <button v-else type="button" @click="item.command?.()">{{ item.label }}</button>
    </template>
  </div>`,
})

function conversation(overrides: Partial<Conversation> & { id: string }): Conversation {
  return {
    title: `Conversation ${overrides.id}`,
    created_at: '2026-01-01T00:00:00Z',
    is_pinned: false,
    is_favourite: false,
    is_archived: false,
    model: null,
    last_activity_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function mountList(conversations: Conversation[]): VueWrapper {
  return mount(ConversationList, {
    props: { conversations },
    global: {
      plugins: [PrimeVue],
      directives: { tooltip: Tooltip },
      stubs: { Menu: MenuStub },
    },
  })
}

async function openMenu(wrapper: VueWrapper, index = 0): Promise<void> {
  await wrapper.findAll('button[aria-label="Conversation actions"]')[index]!.trigger('click')
}

function menuItem(wrapper: VueWrapper, label: string): DOMWrapper<Element> {
  return wrapper.findAll('.menu-stub button').find((button) => button.text() === label)!
}

function renameField(wrapper: VueWrapper): DOMWrapper<Element> {
  return wrapper.find('input[aria-label="Conversation title"]')
}

describe('ConversationList rows', () => {
  it('badges a favourite row and no other', () => {
    const wrapper = mountList([
      conversation({ id: 'a', is_favourite: true }),
      conversation({ id: 'b' }),
    ])

    const rows = wrapper.findAll('li')
    expect(rows[0]!.find('[aria-label="Favourite"]').exists()).toBe(true)
    expect(rows[1]!.find('[aria-label="Favourite"]').exists()).toBe(false)
  })

  it('states the archived state in the row, not in colour alone', () => {
    const wrapper = mountList([conversation({ id: 'a', title: 'Old chat', is_archived: true })])

    expect(wrapper.find('.sr-only').text()).toBe('(archived)')
  })

  it('says nothing about archiving on an active row', () => {
    const wrapper = mountList([conversation({ id: 'a' })])

    expect(wrapper.find('.sr-only').exists()).toBe(false)
  })

  it('selects a row through the model', async () => {
    const wrapper = mountList([conversation({ id: 'a', title: 'First' })])

    await wrapper.find('button:not([aria-label])').trigger('click')

    expect(wrapper.emitted('update:activeId')).toEqual([['a']])
  })

  it('marks the selected row for assistive technology', () => {
    const wrapper = mount(ConversationList, {
      props: { conversations: [conversation({ id: 'a', title: 'First' })], activeId: 'a' },
      global: {
        plugins: [PrimeVue],
        directives: { tooltip: Tooltip },
        stubs: { Menu: MenuStub },
      },
    })

    expect(wrapper.find('button[aria-current="true"]').exists()).toBe(true)
  })
})

describe('ConversationList inline rename', () => {
  it('turns the row into a field and saves on Enter', async () => {
    const wrapper = mountList([conversation({ id: 'a', title: 'First' })])
    await openMenu(wrapper)

    expect(renameField(wrapper).exists()).toBe(false)
    await menuItem(wrapper, 'Rename').trigger('click')

    const field = renameField(wrapper)
    expect(field.exists()).toBe(true)
    expect((field.element as HTMLInputElement).value).toBe('First')

    await field.setValue('  Renamed  ')
    await field.trigger('keydown.enter')

    expect(wrapper.emitted('rename')).toEqual([['a', 'Renamed']])
    expect(renameField(wrapper).exists()).toBe(false)
    expect(wrapper.text()).toContain('First')
  })

  it('cancels on Escape without writing anything', async () => {
    const wrapper = mountList([conversation({ id: 'a', title: 'First' })])
    await openMenu(wrapper)
    await menuItem(wrapper, 'Rename').trigger('click')

    await renameField(wrapper).setValue('Renamed')
    await renameField(wrapper).trigger('keydown.esc')

    expect(wrapper.emitted('rename')).toBeUndefined()
    expect(renameField(wrapper).exists()).toBe(false)
    expect(wrapper.text()).toContain('First')
  })

  it('closes without a write when the title is blank or unchanged', async () => {
    const wrapper = mountList([conversation({ id: 'a', title: 'First' })])
    await openMenu(wrapper)
    await menuItem(wrapper, 'Rename').trigger('click')

    await renameField(wrapper).setValue('   ')
    await renameField(wrapper).trigger('keydown.enter')

    expect(wrapper.emitted('rename')).toBeUndefined()
    expect(renameField(wrapper).exists()).toBe(false)

    await openMenu(wrapper)
    await menuItem(wrapper, 'Rename').trigger('click')
    await renameField(wrapper).setValue('First')
    await renameField(wrapper).trigger('keydown.enter')

    expect(wrapper.emitted('rename')).toBeUndefined()
  })
})

describe('ConversationList menu', () => {
  it('offers the inverse of every state', async () => {
    const wrapper = mountList([
      conversation({ id: 'a', is_pinned: true, is_favourite: true, is_archived: true }),
    ])

    await openMenu(wrapper)

    expect(wrapper.findAll('.menu-stub button').map((button) => button.text())).toEqual([
      'Rename',
      'Unpin',
      'Remove from favourites',
      'Unarchive',
      'Delete',
    ])
  })

  it('offers the additive wording when nothing is set', async () => {
    const wrapper = mountList([conversation({ id: 'a' })])

    await openMenu(wrapper)

    expect(wrapper.findAll('.menu-stub button').map((button) => button.text())).toEqual([
      'Rename',
      'Pin',
      'Add to favourites',
      'Archive',
      'Delete',
    ])
  })

  it('emits each action with its row', async () => {
    const wrapper = mountList([conversation({ id: 'a', title: 'First' })])
    await openMenu(wrapper)

    await menuItem(wrapper, 'Pin').trigger('click')
    await menuItem(wrapper, 'Add to favourites').trigger('click')
    await menuItem(wrapper, 'Archive').trigger('click')
    await menuItem(wrapper, 'Delete').trigger('click')

    expect(wrapper.emitted('togglePin')).toEqual([['a']])
    expect(wrapper.emitted('toggleFavourite')).toEqual([['a']])
    expect(wrapper.emitted('toggleArchive')).toEqual([['a']])
    expect(wrapper.emitted('remove')?.[0]?.[0]).toMatchObject({ id: 'a', title: 'First' })
  })
})
