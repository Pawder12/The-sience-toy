extends Node2D

const PlayerScene := preload("res://scripts/Player.gd")
const EnemyScene := preload("res://scripts/Enemy.gd")
const HudScene := preload("res://scripts/Hud.gd")

var player: Player
var hud: Hud
var enemies: Array[Enemy] = []
var game_finished := false


func _ready() -> void:
	_build_arena()
	_spawn_player()
	_spawn_enemies()
	_build_hud()
	queue_redraw()


func _process(_delta: float) -> void:
	if game_finished and Input.is_key_pressed(KEY_R):
		get_tree().reload_current_scene()


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(1600.0, 720.0)), Color(0.04, 0.06, 0.1))
	for x in range(0, 1601, 80):
		draw_line(Vector2(x, 0.0), Vector2(x, 720.0), Color(0.07, 0.1, 0.16), 1.0)
	for y in range(0, 721, 80):
		draw_line(Vector2(0.0, y), Vector2(1600.0, y), Color(0.07, 0.1, 0.16), 1.0)


func _build_arena() -> void:
	_create_platform(Rect2(0.0, 640.0, 1600.0, 80.0), Color(0.12, 0.17, 0.24))
	_create_platform(Rect2(0.0, 0.0, 24.0, 720.0), Color(0.12, 0.17, 0.24))
	_create_platform(Rect2(1576.0, 0.0, 24.0, 720.0), Color(0.12, 0.17, 0.24))
	_create_platform(Rect2(220.0, 500.0, 240.0, 28.0), Color(0.16, 0.23, 0.33))
	_create_platform(Rect2(600.0, 420.0, 260.0, 28.0), Color(0.16, 0.23, 0.33))
	_create_platform(Rect2(980.0, 510.0, 260.0, 28.0), Color(0.16, 0.23, 0.33))
	_create_platform(Rect2(1320.0, 390.0, 180.0, 28.0), Color(0.16, 0.23, 0.33))
	_create_platform(Rect2(720.0, 590.0, 70.0, 50.0), Color(0.22, 0.26, 0.31))
	_create_platform(Rect2(840.0, 590.0, 70.0, 50.0), Color(0.22, 0.26, 0.31))


func _spawn_player() -> void:
	player = PlayerScene.new()
	player.global_position = Vector2(130.0, 560.0)
	player.health_changed.connect(_on_player_health_changed)
	player.died.connect(_on_player_died)
	add_child(player)

	var camera := Camera2D.new()
	camera.zoom = Vector2(0.9, 0.9)
	camera.position_smoothing_enabled = true
	camera.position_smoothing_speed = 8.0
	player.add_child(camera)
	camera.make_current()


func _spawn_enemies() -> void:
	for enemy_position in [
		Vector2(430.0, 450.0),
		Vector2(770.0, 370.0),
		Vector2(1130.0, 460.0),
		Vector2(1410.0, 340.0),
	]:
		var enemy := EnemyScene.new()
		enemy.global_position = enemy_position
		enemy.setup(player)
		enemy.died.connect(_on_enemy_died)
		enemies.append(enemy)
		add_child(enemy)


func _build_hud() -> void:
	hud = HudScene.new()
	add_child(hud)
	hud.set_health(player.health, player.max_health)
	hud.set_enemies_remaining(enemies.size())


func _create_platform(rect: Rect2, color: Color) -> void:
	var body := StaticBody2D.new()
	body.position = rect.position + rect.size * 0.5
	body.collision_layer = 1
	body.collision_mask = 0

	var shape := RectangleShape2D.new()
	shape.size = rect.size
	var collision_shape := CollisionShape2D.new()
	collision_shape.shape = shape
	body.add_child(collision_shape)
	add_child(body)

	var visual := ColorRect.new()
	visual.position = rect.position
	visual.size = rect.size
	visual.color = color
	add_child(visual)


func _on_player_health_changed(current: int, maximum: int) -> void:
	if is_instance_valid(hud):
		hud.set_health(current, maximum)


func _on_player_died() -> void:
	game_finished = true
	if is_instance_valid(hud):
		hud.set_game_over()


func _on_enemy_died(enemy: Enemy) -> void:
	enemies.erase(enemy)
	if is_instance_valid(hud):
		hud.set_enemies_remaining(enemies.size())
	if enemies.is_empty():
		game_finished = true
