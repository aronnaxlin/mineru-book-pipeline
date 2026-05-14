PYTHON     := python3
DOCS_OUT   := docs
REPORTS    := reports

.PHONY: all export lint fmt-check fingerprint serve build deploy clean help

all: export lint fmt-check fingerprint build

## export: Run mineru-export with book.yml
export:
	mineru-export book.yml

## lint: Run markdownlint-cli2 on all docs
lint:
	markdownlint-cli2 "docs/**/*.md"

## fmt-check: Check Markdown formatting with mdformat
fmt-check:
	mdformat --check docs/chapters/

## fmt: Auto-fix Markdown formatting with mdformat
fmt:
	mdformat docs/chapters/

## fingerprint: Generate/diff SHA-256 fingerprints for docs/
fingerprint:
	$(PYTHON) -m mineru_pipeline.fingerprint --docs-dir $(DOCS_OUT) --out $(REPORTS)/fingerprints.json

## serve: Start MkDocs dev server
serve:
	mkdocs serve

## build: Build static site
build:
	mkdocs build --strict

## deploy: Build and deploy to Cloudflare Pages
## Set PAGES_PROJECT to your project name before running.
deploy: build
	npx wrangler pages deploy site --project-name $(PAGES_PROJECT) --branch main --commit-dirty=true

## clean: Remove generated docs/chapters, docs/images, site/, reports/
clean:
	rm -rf docs/chapters docs/images site $(REPORTS)/fingerprints.json

## help: Show this help
help:
	@grep -E '^##' Makefile | sed 's/## /  /'
