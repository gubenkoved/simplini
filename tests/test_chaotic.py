import configparser
import logging
import random
import string
import unittest
from typing import Callable, Dict, Optional

import simplini
from tests.common import CaseBase

LOGGER = logging.getLogger(__name__)


class ChaosTest(CaseBase):
    def random_id(self, random_gen: random.Random, min_len: int = 5, max_len: int = 10):
        return "".join(
            random_gen.choice(string.ascii_letters + string.digits)
            for _ in range(random_gen.randint(min_len, max_len))
        )

    def create_document_chaotic(
        self,
        random_gen: random.Random,
        eof_chance: float = 0.05,
    ):
        tokens = {
            "new_line": lambda: "\n",
            "random_identifier": lambda: self.random_id(random_gen),
            "eq": lambda: "=",
            "whitespace": lambda: " ",
            "quote": lambda: '"',
            "comment": lambda: "#",
            "section_header": lambda: f"[{self.random_id(random_gen)}]",
        }

        path = self.get_temp_path()

        with open(path, "w") as f:
            while True:
                val = random_gen.random()

                if val < eof_chance:
                    break

                # pick token at random and write it
                token_type = random_gen.choice(list(tokens))
                token = tokens[token_type]()
                f.write(token)

        return path

    def get_data_with_std(self, path: str) -> Optional[Dict]:
        try:
            # std configparser allows unnamed sections only since Python3.13
            parser = configparser.RawConfigParser()
            parser.read(path)

            data = {
                section: dict(parser.items(section)) for section in parser.sections()
            }

            kv_count = sum(len(section_values) for section_values in data.values())

            if kv_count > 1:
                pass

            return data
        except (
            configparser.ParsingError,
            configparser.DuplicateSectionError,
            configparser.DuplicateOptionError,
        ) as e:
            LOGGER.debug("std error: %r", e, exc_info=True)
            return None

    def get_data_with_simplini(self, path: str):
        try:
            config = simplini.IniConfig.load(path)
            return config.as_dict()
        except simplini.ParsingError as e:
            LOGGER.debug("simplini error: %r", e, exc_info=True)
            return None

    def ensure_can_read_if_config_parser_can_read(self, path: str):
        configparser_data = self.get_data_with_std(path)
        simplini_data = self.get_data_with_simplini(path)

        if configparser_data is not None:
            self.assertIsNotNone(simplini_data)
            self.assertEqual(configparser_data, simplini_data)

    def run_chaotic_test(
        self, iterations: int, master_seed: int, test_fn: Callable[[int], None]
    ):
        meta_gen = random.Random()
        meta_gen.seed(master_seed)

        for idx in range(iterations):
            with self.subTest(idx=idx):
                iteration_seed = meta_gen.randint(0, 10**9)
                LOGGER.info("iteration #%d, seed is %s", idx, iteration_seed)
                try:
                    test_fn(iteration_seed)
                except Exception as e:
                    LOGGER.error(
                        "Chaotic test failed on iteration %s with message '%s'. "
                        "Reproduce the same case by passing %s seed value to %s.",
                        idx,
                        e,
                        iteration_seed,
                        test_fn.__name__,
                    )
                    raise

    def test_sanity(self):
        def impl(seed: int):
            iteration_gen = random.Random()
            iteration_gen.seed(seed)

            path = self.create_document_chaotic(iteration_gen)

            with open(path, "r") as f:
                config_text = f.read()

            LOGGER.debug("config: %s\n", config_text)

            data = self.get_data_with_simplini(path)
            LOGGER.debug(data)

        self.run_chaotic_test(
            iterations=1000,
            master_seed=42,
            test_fn=impl,
        )

    # it is currently reproducing quite wierd behaviours from
    # configparser which is not useful to carry over, so disable the test for now
    @unittest.skip("skip")
    def test_chaotic(self):
        def impl(seed: int):
            random_gen = random.Random()
            random_gen.seed(seed)

            path = self.create_document_chaotic(random_gen)

            with open(path, "r") as f:
                config_text = f.read()

            LOGGER.debug("config:\n%s", config_text)

            self.ensure_can_read_if_config_parser_can_read(path)

        self.run_chaotic_test(
            iterations=1000,
            master_seed=42,
            test_fn=impl,
        )
