from abc import ABC, abstractmethod
import argparse

class UWBProcessor(ABC):
	name: str = "base"
	help: str = "Base processor (not usable directly)"

	@classmethod
	def add_cli(cls, subparsers: argparse._SubParsersAction) -> None:
		parser: argparse.ArgumentParser = subparsers.add_parser(cls.name, help=cls.help, description=cls.help)
		parser.set_defaults(processor_class=cls)
		cls.cli(parser)

	@classmethod
	@abstractmethod
	def cli(cls, parser: argparse.ArgumentParser) -> None:
		"""Füge hier cli Argumente hinzu"""
		pass

	@abstractmethod
	def on_data(self, i: int, line: str):
		"""Wird aufgerufen jedes mal wenn neue Daten kommen"""
		pass

	@abstractmethod
	def main(self):
		"""Wird solange das Programm läuft, wiederholt auf dem Main-Thread aufgerufen"""
		pass