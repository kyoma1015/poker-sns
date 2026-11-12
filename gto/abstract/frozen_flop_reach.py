"""Read-only reach extraction for frozen HU50BB preflop strategies.

This adapter computes class reach for one facing-3bet or facing-4bet node.
It never updates the strategy and never invents showdown equities.
"""
import math
from gto.abstract.model import tree, chance, classes
from gto.abstract.precision import frozen_rows


def frozen_reach(stage, strategy, *, after_call=False):
    if stage not in ("vs_3bet", "vs_4bet"):
        raise ValueError("unsupported stage")
    nodes = tree()
    n = 169
    if len(strategy) != len(nodes)*3*n:
        raise ValueError("strategy dimensions do not match HU50BB tree")
    if any(not isinstance(v, (float, int)) or not math.isfinite(v) or v < 0 or v > 1 for v in strategy):
        raise ValueError("invalid strategy probabilities")
    frozen_rows(strategy,nodes,n)
    target_raises = 2 if stage == "vs_3bet" else 3
    found = []
    def visit(index, seat0, seat1):
        node = nodes[index]
        if node["actor"] < 0:
            return
        if node["raises"] == target_raises and "call" not in node["history"]:
            found.append((index, node["actor"], seat0, seat1))
            return
        actor = node["actor"]
        for a, child in enumerate(node["children"]):
            weights = [strategy[(index*3+a)*n+h] for h in range(n)]
            visit(child,
                  [x*y for x,y in zip(seat0,weights)] if actor == 0 else seat0,
                  [x*y for x,y in zip(seat1,weights)] if actor == 1 else seat1)
    visit(0, [1.]*n, [1.]*n)
    if len(found) != 1:
        raise ValueError("expected exactly one decision node")
    index, actor, seat0, seat1 = found[0]
    node=nodes[index]
    _, p = chance(classes())
    before_mass=math.fsum(p[i*n+j]*seat0[i]*seat1[j] for i in range(n) for j in range(n))
    matched=max(node["contributions"])
    if after_call:
        action=node["actions"].index("call")
        call=[strategy[(index*3+action)*n+h] for h in range(n)]
        if actor==0:seat0=[x*y for x,y in zip(seat0,call)]
        else:seat1=[x*y for x,y in zip(seat1,call)]
    # The downstream evaluator always indexes hero (decision actor) first.
    if actor == 0:
        hero, villain = seat0, seat1
        ordered_p = p
    else:
        hero, villain = seat1, seat0
        ordered_p = [p[j*n+i] for i in range(n) for j in range(n)]
    mass = math.fsum(ordered_p[i*n+j]*hero[i]*villain[j] for i in range(n) for j in range(n))
    if mass <= 0:
        raise ValueError("target stage has no reach")
    return {"stage": stage, "node_index": index, "hero_actor": actor,
            "class_probability": ordered_p, "hero_reach": hero,
            "villain_reach": villain, "conditional_mass": mass,
            "conditioned_on_call": after_call,
            "before_call_mass": before_mass,
            "post_call_pot_bb": float(matched),
            "matched_contribution_bb": matched/2.,
            "remaining_stack_bb": (100-matched)/2.,
            "history": list(node["history"]),
            "frozen_strategy": True, "equity_by_pair": None,
            "equity_status": "REQUIRED_NOT_DERIVED",
            "full_game_gto_verified": False}
