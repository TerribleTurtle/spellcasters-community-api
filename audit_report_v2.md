# Audit Report V2

## Validation Failures
None.

## Consistency Outliers (Z-Score > 3.0)
- Schema `spells.schema.json`: Field `cast_time` has value `0.5` in `fire_ball` (Z-Score: 4.01, Mean: 0.03)
- Schema `units.schema.json`: Field `health` has value `10000` in `juggernaut` (Z-Score: 4.20, Mean: 1198.12)
- Schema `units.schema.json`: Field `recharge_time` has value `120` in `juggernaut` (Z-Score: 3.04, Mean: 32.54)

## Orphaned Schemas
- audit.schema.json
- changelog_index.schema.json
- status.schema.json
- definitions/core.schema.json
- all_data.schema.json
- definitions/mechanics/infusion.schema.json
- definitions/resource.schema.json
- definitions/magic.schema.json
- definitions/mechanics/feature.schema.json
- definitions/mechanics/damage_reduction.schema.json
- definitions/stats.schema.json
- definitions/enums.schema.json
- definitions/ability.schema.json
- definitions/mechanics/aura.schema.json
- definitions/mechanics/initial_attack.schema.json
- changelog.schema.json
- patches.schema.json
- definitions/mechanics/weak_point.schema.json
- definitions/mechanics.schema.json
- timeline_entry.schema.json
- definitions/mechanics/bonus_damage.schema.json
- definitions/mechanics/spawner.schema.json
- definitions/mechanics/damage_modifier.schema.json
- infusions.schema.json

## Mapping
|  | game_config.json | game_config.schema.json | High (Explicit) |
|  | game_systems.json | game_systems.schema.json | High (Explicit) |
|  | infusions.json | NONE | None |
|  | patches.json | NONE | None |
|  | queue.json | NONE | None |
| consumables | cast_stone_fire_ball.json | consumables.schema.json | High (Explicit) |
| consumables | cast_stone_heal_ray.json | consumables.schema.json | High (Explicit) |
| consumables | charge_orb_1.json | consumables.schema.json | High (Explicit) |
| consumables | charge_orb_2.json | consumables.schema.json | High (Explicit) |
| consumables | conquest_banner.json | consumables.schema.json | High (Explicit) |
| consumables | healing_grimoire_1.json | consumables.schema.json | High (Explicit) |
| consumables | healing_grimoire_2.json | consumables.schema.json | High (Explicit) |
| consumables | healing_grimoire_3.json | consumables.schema.json | High (Explicit) |
| consumables | power_grimoire.json | consumables.schema.json | High (Explicit) |
| consumables | protection_grimoire.json | consumables.schema.json | High (Explicit) |
| heroes | astral_monk.json | heroes.schema.json | High (Explicit) |
| heroes | fire_elementalist.json | heroes.schema.json | High (Explicit) |
| heroes | iron_sorcerer.json | heroes.schema.json | High (Explicit) |
| heroes | mystic_scribe.json | heroes.schema.json | High (Explicit) |
| heroes | stone_shaman.json | heroes.schema.json | High (Explicit) |
| heroes | swamp_witch.json | heroes.schema.json | High (Explicit) |
| map_chests | mausoleum.json | map_chests.schema.json | High (Explicit) |
| map_chests | nordic_shore.json | map_chests.schema.json | High (Explicit) |
| spells | astral_nova.json | spells.schema.json | High (Explicit) |
| spells | astral_shot.json | spells.schema.json | High (Explicit) |
| spells | earthquake.json | spells.schema.json | High (Explicit) |
| spells | fire_ball.json | spells.schema.json | High (Explicit) |
| spells | fire_rain.json | spells.schema.json | High (Explicit) |
| spells | fire_ray.json | spells.schema.json | High (Explicit) |
| spells | flame_surge.json | spells.schema.json | High (Explicit) |
| spells | frost_surge.json | spells.schema.json | High (Explicit) |
| spells | grand_lightning.json | spells.schema.json | High (Explicit) |
| spells | heal_ray.json | spells.schema.json | High (Explicit) |
| spells | holy_arrow.json | spells.schema.json | High (Explicit) |
| spells | ice_ray.json | spells.schema.json | High (Explicit) |
| spells | metamorphosis.json | spells.schema.json | High (Explicit) |
| spells | poison_breath.json | spells.schema.json | High (Explicit) |
| spells | poison_grenade.json | spells.schema.json | High (Explicit) |
| spells | resurrection.json | spells.schema.json | High (Explicit) |
| spells | sacrifice.json | spells.schema.json | High (Explicit) |
| spells | thunder_ray.json | spells.schema.json | High (Explicit) |
| titans | gaia_beast.json | titans.schema.json | High (Explicit) |
| titans | thanatos.json | titans.schema.json | High (Explicit) |
| units | astral_tower.json | units.schema.json | High (Explicit) |
| units | ballista.json | units.schema.json | High (Explicit) |
| units | crypt.json | units.schema.json | High (Explicit) |
| units | dryad.json | units.schema.json | High (Explicit) |
| units | earth_golem.json | units.schema.json | High (Explicit) |
| units | faerie.json | units.schema.json | High (Explicit) |
| units | giant_shielder.json | units.schema.json | High (Explicit) |
| units | harpy.json | units.schema.json | High (Explicit) |
| units | harpy_nest.json | units.schema.json | High (Explicit) |
| units | juggernaut.json | units.schema.json | High (Explicit) |
| units | lich.json | units.schema.json | High (Explicit) |
| units | lizard_archer.json | units.schema.json | High (Explicit) |
| units | ogre.json | units.schema.json | High (Explicit) |
| units | rampart.json | units.schema.json | High (Explicit) |
| units | rhino_rider.json | units.schema.json | High (Explicit) |
| units | rocket_soldier.json | units.schema.json | High (Explicit) |
| units | rocket_soldier_factory.json | units.schema.json | High (Explicit) |
| units | ruin_spider.json | units.schema.json | High (Explicit) |
| units | siren.json | units.schema.json | High (Explicit) |
| units | skeleton_warrior.json | units.schema.json | High (Explicit) |
| units | steam_tank.json | units.schema.json | High (Explicit) |
| units | stone_behemoth.json | units.schema.json | High (Explicit) |
| units | wolven_hunter.json | units.schema.json | High (Explicit) |
| units | wyvern.json | units.schema.json | High (Explicit) |
| upgrades | conqueror.json | upgrades.schema.json | High (Explicit) |
| upgrades | duelist.json | upgrades.schema.json | High (Explicit) |
| upgrades | enchanter.json | upgrades.schema.json | High (Explicit) |
