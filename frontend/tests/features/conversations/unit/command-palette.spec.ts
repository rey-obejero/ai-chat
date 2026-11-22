import { mount, type VueWrapper } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import CommandPalette from '@/features/conversations/components/CommandPalette.vue'
import { COMMANDS, commandOptionId, type Command } from '@/features/conversations/commands'

function mountPalette(commands: Command[] = COMMANDS, activeIndex = 0): VueWrapper {
  return mount(CommandPalette, { props: { commands, activeIndex } })
}

describe('CommandPalette', () => {
  it('renders one named listbox row per command', () => {
    const wrapper = mountPalette()

    expect(wrapper.find('[role="listbox"]').attributes('aria-label')).toBe('Commands')
    // The composer points its `aria-controls` at this id.
    expect(wrapper.find('[role="listbox"]').attributes('id')).toBe('command-palette')

    const rows = wrapper.findAll('[role="option"]')
    expect(rows.map((row) => row.attributes('id'))).toEqual(COMMANDS.map(commandOptionId))

    for (const [index, row] of rows.entries()) {
      const command = COMMANDS[index]
      expect(row.text()).toContain(command.label)
      expect(row.text()).toContain(command.description)
    }
  })

  it('marks only the highlighted row as selected', async () => {
    const wrapper = mountPalette()

    const selected = (): string[] =>
      wrapper
        .findAll('[role="option"]')
        .filter((row) => row.attributes('aria-selected') === 'true')
        .map((row) => row.attributes('id') ?? '')

    expect(selected()).toEqual([commandOptionId(COMMANDS[0])])

    await wrapper.setProps({ activeIndex: 2 })

    expect(selected()).toEqual([commandOptionId(COMMANDS[2])])
  })

  it('emits select with the clicked command', async () => {
    const wrapper = mountPalette()

    await wrapper.findAll('[role="option"]')[1].trigger('click')

    expect(wrapper.emitted('select')).toEqual([[COMMANDS[1]]])
  })

  it('emits close when Escape reaches a row', async () => {
    const wrapper = mountPalette()

    await wrapper.findAll('[role="option"]')[0].trigger('keydown', { key: 'Escape' })

    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('states an empty result instead of an empty popup', () => {
    const wrapper = mountPalette([])

    expect(wrapper.findAll('[role="option"]')).toHaveLength(0)
    expect(wrapper.find('[role="listbox"]').exists()).toBe(false)
    expect(wrapper.find('[role="status"]').text()).toBe('No matching commands.')
  })
})
