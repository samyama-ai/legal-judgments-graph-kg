"""Build and load the legal-judgments graph into Samyama.

Reads files from ./data, applies schema/legal_judgments_kg.cypher, and loads
nodes/edges via the Samyama graph engine.
"""
import click


@click.command()
@click.option("--limit", type=int, default=None, help="Cap rows per source for a fast demo load.")
def main(limit):
    # TODO:
    #   1. connect to the Samyama graph engine
    #   2. run schema/legal_judgments_kg.cypher
    #   3. load Judgment / Court / Judge / Statute / Party nodes
    #   4. load DECIDED_BY / HEARD_IN / INVOKES_STATUTE / INVOLVES_PARTY / CITES edges
    print(f"[loader] loading legal-judgments KG (limit={limit}) ...")


if __name__ == "__main__":
    main()
