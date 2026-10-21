# Changelog

## [0.3.0](https://github.com/rey-obejero/ai-chat/compare/v0.2.0...v0.3.0) (2026-10-21)


### Features

* add message actions with a generation gate and idempotent writes ([926e19a](https://github.com/rey-obejero/ai-chat/commit/926e19a06e7624bf8e30a022e340385d74fd599d))
* add the slash-command palette ([6b7cac6](https://github.com/rey-obejero/ai-chat/commit/6b7cac6c38ab494b470c2400c04df060b9759fc9))
* **back-end:** add the display-name columns to users ([30c4eb2](https://github.com/rey-obejero/ai-chat/commit/30c4eb2786bd8e60c0f35d5c902667b14c6a4b00))
* **back-end:** derive, normalise and reject display names ([e48665e](https://github.com/rey-obejero/ai-chat/commit/e48665e39a2bd80e74e52fb9849a4c1e22f628a1))
* **back-end:** enforce screening and verification at the SDK boundary ([364cd5c](https://github.com/rey-obejero/ai-chat/commit/364cd5cb980bbcd03a1c9403dc67a339a349c061))
* **back-end:** expose the display name and prompt flag over /me ([1a37401](https://github.com/rey-obejero/ai-chat/commit/1a37401ba50ab530617c0780e42c1079007d8039))
* **back-end:** reduce the allowance until the email is verified ([8e0cf9b](https://github.com/rey-obejero/ai-chat/commit/8e0cf9b831acd7a4a3bcbfe0ae0cd1d7c022b07f))
* **back-end:** report and cache the email verification state ([e2ad13e](https://github.com/rey-obejero/ai-chat/commit/e2ad13e62199cea1f3b173fdb0699e7604f5186e))
* **back-end:** screen passwords for strength and breach data ([aabe503](https://github.com/rey-obejero/ai-chat/commit/aabe5037cee4a59f4ce4f53dfd8e5285e70a2a16))
* conversation management: search, rename, delete, and states ([90688b0](https://github.com/rey-obejero/ai-chat/commit/90688b018580741ee412d7b074a105778b46d697))
* **front-end:** add the name prompt and the Profile field ([3ff7bfe](https://github.com/rey-obejero/ai-chat/commit/3ff7bfe2f61625490a9394f9e4f8e8f8e85621a4))
* **front-end:** add the verification route and the unverified nudge ([2bd1f9b](https://github.com/rey-obejero/ai-chat/commit/2bd1f9b9341b4a39e2aca47be90315386d15bfd7))
* **front-end:** explain a reduced allowance where it is shown ([0436e51](https://github.com/rey-obejero/ai-chat/commit/0436e510aeb9bf060150961ff73ec066353535ac))
* personalise the assistant per account and per conversation ([af8fe3a](https://github.com/rey-obejero/ai-chat/commit/af8fe3aa398cd69ce376eb9ba9e8de48368b8f56))
* render assistant markdown and proxy external images ([6ce1e6a](https://github.com/rey-obejero/ai-chat/commit/6ce1e6a82229cba72e86f5b84bf79bbf60416a2f))


### Bug Fixes

* **back-end:** carry a refused name's reason in the problem detail ([131908e](https://github.com/rey-obejero/ai-chat/commit/131908ee51066111d865fc6c1dd38c267a7bad07))
* **back-end:** screen a passphrase longer than the scorer reads ([56e11d4](https://github.com/rey-obejero/ai-chat/commit/56e11d47def0bfa42b065a668c5a522308d6b598))
* **conversations:** keep a reply's spend when its conversation is deleted ([23bb4c7](https://github.com/rey-obejero/ai-chat/commit/23bb4c7642043b1fb923223cd14da5bb4819f9e6))
* **conversations:** make a second edit of a turn a new attempt ([2a3ec9e](https://github.com/rey-obejero/ai-chat/commit/2a3ec9e45d73358510a9779d111a5549a3dd4ade))
* **conversations:** place a mid-stream model caption after the answer ([e8d5450](https://github.com/rey-obejero/ai-chat/commit/e8d5450f459c88134fb4c13ac8e41c6472d3b574))
* **front-end:** focus the name prompt's field ([33f764d](https://github.com/rey-obejero/ai-chat/commit/33f764d6bd6e16cec6849a963c682f6553cbbb8a))
* **front-end:** keep an auth token out of the history entry ([56eb4e2](https://github.com/rey-obejero/ai-chat/commit/56eb4e209db9589757800ecac61b63e4dd73f90c))
* **front-end:** keep the rename field open when the write is refused ([00a4365](https://github.com/rey-obejero/ai-chat/commit/00a4365fe3cf1501b1e7a4fec8b0f7aaaea6ed9b))
* **front-end:** open the command palette where nothing clips it ([a558c16](https://github.com/rey-obejero/ai-chat/commit/a558c164e06c2d2a8f230636b74136d246702b2e))
* **front-end:** re-read the transcript after a failed edit or regenerate ([df680fd](https://github.com/rey-obejero/ai-chat/commit/df680fda05a6b1a4ebf2551c825594df764b98f1))
* **front-end:** read the open conversation from every row the session saw ([6748de8](https://github.com/rey-obejero/ai-chat/commit/6748de844a4f7ae5540f56ae158c2227bb966f66))
* **front-end:** reveal sidebar chevron and correct button font sizes ([c375621](https://github.com/rey-obejero/ai-chat/commit/c37562113b8fb7f1155e9f8a8552ef05d7e75c23))
* **media:** bound the proxied fetch and keep the 502 contract ([777f6fb](https://github.com/rey-obejero/ai-chat/commit/777f6fb8c6de3d99e88ca362fae5a081d56b95ee))

## [0.2.0](https://github.com/rey-obejero/ai-chat/compare/v0.1.0...v0.2.0) (2026-10-07)


### Features

* **self-host:** add the self-hosted production stack behind Caddy ([6b49b05](https://github.com/rey-obejero/ai-chat/commit/6b49b05d7a1780751b1fc233a9312293524032e9))


### Bug Fixes

* **release:** use the existing v-prefixed tag format ([9193389](https://github.com/rey-obejero/ai-chat/commit/91933894a252ebe15fdddcd20997f4f1aa229628))
