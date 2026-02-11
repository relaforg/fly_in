MYPY_FLAGS = --warn-return-any \
			 --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs \
			 --check-untyped-defs

run:
	@python3 srcs/main.py $(ARGS)

install:
	@pip install -r requirements.txt

debug:
	@python3 -m pdb -m srcs

clean:
	rm -f  __pycache__ .mypy_cache

lint:
	@python3 -m flake8 srcs
	@python3 -m mypy srcs $(MYPY_FLAGS)

lint-strict:
	@python3 -m flake8 srcs
	@python3 -m mypy srcs --strict
