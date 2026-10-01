extends Node2D

@onready var eyes: Sprite2D = $Eyes
@onready var brows: Sprite2D = $Brows
@onready var mouth: Sprite2D = $Mouth
@onready var blush: Sprite2D = $Blush
@onready var blink_timer: Timer = $BlinkTimer

var eye_textures := {
	"open": preload("res://assets/portrait/eyes_open.png"),
	"half": preload("res://assets/portrait/eyes_half.png"),
	"closed": preload("res://assets/portrait/eyes_closed.png"),
}
var mouth_textures := {
	"neutral": preload("res://assets/portrait/mouth_neutral.png"),
	"smile": preload("res://assets/portrait/mouth_smile.png"),
}
var brow_textures := {
	"neutral": preload("res://assets/portrait/brows_neutral.png"),
	"raised": preload("res://assets/portrait/brows_raised.png"),
	"furrowed": preload("res://assets/portrait/brows_furrowed.png"),
}

var _current_eye_key: String = "open"
var _is_blinking: bool = false


func _ready() -> void:
	_start_breathing()
	blink_timer.timeout.connect(_do_blink)
	_schedule_next_blink()


func _start_breathing() -> void:
	var tween := create_tween().set_loops()
	tween.tween_property(self, "scale:y", 1.015, 1.5) \
		.set_ease(Tween.EASE_IN_OUT) \
		.set_trans(Tween.TRANS_SINE)
	tween.tween_property(self, "scale:y", 1.0, 1.5) \
		.set_ease(Tween.EASE_IN_OUT) \
		.set_trans(Tween.TRANS_SINE)


func _schedule_next_blink() -> void:
	blink_timer.start(randf_range(2.0, 6.0))


func _do_blink() -> void:
	_is_blinking = true
	eyes.texture = eye_textures["half"]
	await get_tree().create_timer(0.05).timeout
	eyes.texture = eye_textures["closed"]
	await get_tree().create_timer(0.1).timeout
	eyes.texture = eye_textures["half"]
	await get_tree().create_timer(0.05).timeout
	eyes.texture = eye_textures[_current_eye_key]
	_is_blinking = false
	_schedule_next_blink()


func set_expression(
	eye_key: String = "open",
	mouth_key: String = "neutral",
	brow_key: String = "neutral"
) -> void:
	if eye_key in eye_textures:
		_current_eye_key = eye_key
		if not _is_blinking:
			eyes.texture = eye_textures[eye_key]
	if mouth_key in mouth_textures:
		mouth.texture = mouth_textures[mouth_key]
	if brow_key in brow_textures:
		brows.texture = brow_textures[brow_key]


func set_blush(intensity: float) -> void:
	blush.modulate.a = clampf(intensity, 0.0, 1.0)
