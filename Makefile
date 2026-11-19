.PHONY: dev lint test test-integration cov up down logs reset

dev:
	uv run poe dev

lint:
	uv run poe lint

test:
	uv run poe test

test-integration:
	uv run poe test-integration

cov:
	uv run poe cov

up:
	uv run poe up

down:
	uv run poe down

logs:
	uv run poe logs

reset:
	uv run poe reset
