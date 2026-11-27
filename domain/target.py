from config.constants import (
    DEFAULT_TARGET_RULES,
    MASTER_TARGET_FILE,
    TARGET_GROUP_LABELS,
)
from core.storage import _read_json_safe, write_json_atomic


def load_target_rules():
    data = _read_json_safe(MASTER_TARGET_FILE)
    return data if isinstance(data, dict) else dict(DEFAULT_TARGET_RULES)


TARGET_RULES = load_target_rules()


def refresh_target_rules():
    TARGET_RULES.clear()
    TARGET_RULES.update(load_target_rules())
    return TARGET_RULES


def save_target_rules(rules):
    cleaned = rules if isinstance(rules, dict) else {}
    write_json_atomic(MASTER_TARGET_FILE, cleaned)
    refresh_target_rules()


def normalize_brand_key(brand):
    return "".join(str(brand).casefold().split())


def get_brand_target_rule(brand):
    brand_key = normalize_brand_key(brand)
    return next(
        (rule for rule_brand, rule in TARGET_RULES.items() if normalize_brand_key(rule_brand) == brand_key),
        {},
    )


def clean_brand_target_name(brand):
    group = get_brand_target_rule(brand).get("group")
    return TARGET_GROUP_LABELS.get(group, brand)


def get_group_target(group_name, target_key, default_val):
    for rule in TARGET_RULES.values():
        rule_group = rule.get("group")
        if rule_group == "Black_Siro_Kuro":
            rule_group = "Black_Matcha"
        if rule_group == group_name and target_key in rule:
            return rule[target_key]
    return default_val


def get_target_for_brand(brand, target_key, default_val):
    brand_str = str(brand or "").strip()
    if not brand_str:
        return default_val

    for group_key, label in TARGET_GROUP_LABELS.items():
        if brand_str.casefold() == label.casefold():
            canonical_group = "Black_Matcha" if group_key == "Black_Siro_Kuro" else group_key
            return get_group_target(canonical_group, target_key, default_val)

    rule = get_brand_target_rule(brand_str)
    group = rule.get("group")
    if group:
        canonical_group = "Black_Matcha" if group == "Black_Siro_Kuro" else group
        return get_group_target(canonical_group, target_key, default_val)
    return rule.get(target_key, default_val)


def style_status_target(val):
    if val == "Not Achieved":
        return "color: var(--danger-text, #DC2626); font-weight: 700;"
    if val == "Achieved":
        return "color: var(--positive-text, #16A34A); font-weight: 700;"
    return ""
