extends Node2D

@onready var portrait = $Portrait

var _expression_index: int = 0

var _expressions := [
	{"eyes": "open",   "mouth": "neutral", "brows": "neutral",  "blush": 0.0},
	{"eyes": "open",   "mouth": "smile",   "brows": "neutral",  "blush": 0.3},
	{"eyes": "half",   "mouth": "smile",   "brows": "raised",   "blush": 0.7},
	{"eyes": "open",   "mouth": "neutral", "brows": "furrowed",  "blush": 0.0},
	{"eyes": "closed", "mouth": "smile",   "brows": "neutral",  "blush": 1.0},
	{"eyes": "open",   "mouth": "smile",   "brows": "raised",   "blush": 0.0},
]


func _ready() -> void:
	_apply_expression(0)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_expression_index = (_expression_index + 1) % _expressions.size()
		_apply_expression(_expression_index)


func _apply_expression(index: int) -> void:
	var expr = _expressions[index]
	portrait.set_expression(expr["eyes"], expr["mouth"], expr["brows"])
	portrait.set_blush(expr["blush"])
