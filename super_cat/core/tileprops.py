# core/tileprops.py

# Tileset properties: load from JSON and expose helper accessors.

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TileProps:
    # Extendable per-tile properties
    solid: bool = False
    one_way: bool = False
    deadly: bool = False
    spawn: bool = False
    friction: float = 1.0


@dataclass
class TilesetProps:
    tiles: dict[int, TileProps] = field(default_factory=dict)

    @property
    def solid_indices(self) -> set[int]:
        return {idx for idx, props in self.tiles.items() if props.solid}

    @property
    def one_way_indices(self) -> set[int]:
        return {idx for idx, props in self.tiles.items() if props.one_way}

    @property
    def deadly_indices(self) -> set[int]:
        return {idx for idx, props in self.tiles.items() if props.deadly}

    @property
    def spawn_indices(self) -> set[int]:
        return {idx for idx, props in self.tiles.items() if props.spawn}

    def get(self, idx: int) -> TileProps:
        return self.tiles.get(idx, TileProps())


def load_tileset_props(json_path: Path) -> TilesetProps:
    """Load properties JSON and merge with defaults.:
    {
      "default": { "solid": false, "friction": 1.0 },
      "tiles": {
        "0": { "solid": true, "friction": 1.0 },
        "1": { "solid": true },
        "4": { "solid": false, "deadly": false }
      }
    }
    """
    import json

    if not json_path.exists():
        return TilesetProps()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    default = data.get("default", {})
    tiles_raw: dict[str, dict[str, bool | float]] = data.get("tiles", {})

    tiles: dict[int, TileProps] = {}
    for k, v in tiles_raw.items():
        merged = {**default, **v}
        tiles[int(k)] = TileProps(**merged)
    return TilesetProps(tiles)
