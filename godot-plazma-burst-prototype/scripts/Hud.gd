extends CanvasLayer
class_name Hud

var health_label: Label
var status_label: Label
var objective_label: Label


func _ready() -> void:
	health_label = Label.new()
	health_label.position = Vector2(24.0, 18.0)
	health_label.add_theme_font_size_override("font_size", 24)
	add_child(health_label)

	objective_label = Label.new()
	objective_label.position = Vector2(24.0, 50.0)
	objective_label.add_theme_font_size_override("font_size", 18)
	objective_label.text = "A/D or arrows: move   W/Space: jump   Mouse: aim   LMB: fire"
	add_child(objective_label)

	status_label = Label.new()
	status_label.position = Vector2(24.0, 84.0)
	status_label.add_theme_font_size_override("font_size", 22)
	add_child(status_label)


func set_health(current: int, maximum: int) -> void:
	health_label.text = "HP: %d / %d" % [current, maximum]


func set_enemies_remaining(count: int) -> void:
	if count > 0:
		status_label.text = "Neutralize hostiles: %d left" % count
	else:
		status_label.text = "Sector clear. Press R to restart."


func set_game_over() -> void:
	status_label.text = "You are down. Press R to restart."
