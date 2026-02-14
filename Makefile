# Makefile



# --- matrx-cli ─────────────────────────────────────
ship:
	@bash scripts/matrx/ship.sh "$(MSG)"

ship-minor:
	@bash scripts/matrx/ship.sh --minor "$(MSG)"

ship-major:
	@bash scripts/matrx/ship.sh --major "$(MSG)"

ship-status:
	@bash scripts/matrx/ship.sh status

ship-setup:
	@bash scripts/matrx/ship.sh setup $(ARGS)

ship-init:
	@bash scripts/matrx/ship.sh init $(ARGS)

ship-history:
	@bash scripts/matrx/ship.sh history

ship-update:
	@bash scripts/matrx/ship.sh update

ship-help:
	@bash scripts/matrx/ship.sh help

ship-force-remove:
	@bash scripts/matrx/ship.sh force-remove $(ARGS)

env-pull:
	@bash scripts/matrx/env-sync.sh pull

env-push:
	@bash scripts/matrx/env-sync.sh push

env-diff:
	@bash scripts/matrx/env-sync.sh diff

env-status:
	@bash scripts/matrx/env-sync.sh status

env-sync:
	@bash scripts/matrx/env-sync.sh sync

env-pull-force:
	@bash scripts/matrx/env-sync.sh pull --force

env-push-force:
	@bash scripts/matrx/env-sync.sh push --force

tools-update:
	@curl -sL https://raw.githubusercontent.com/armanisadeghi/matrx-ship/main/cli/install.sh | bash

tools-migrate:
	@curl -sL https://raw.githubusercontent.com/armanisadeghi/matrx-ship/main/cli/migrate.sh | bash

.PHONY: ship ship-minor ship-major ship-status ship-setup ship-init ship-history ship-update ship-help ship-force-remove tools-update tools-migrate env-pull env-push env-diff env-status env-sync env-pull-force env-push-force
