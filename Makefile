.PHONY: audit

export OSV_IMAGE ?= ghcr.io/google/osv-scanner:v2.6.0
export OSV_FORMAT ?= vertical

audit:
	@./osv_scan.sh
