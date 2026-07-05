extends CharacterBody2D
class_name Player

signal health_changed(current: int, maximum: int)
signal died

const BulletScene := preload("res://scripts/Bullet.gd")

@export var move_speed: float = 350.0
@export var jump_velocity: float = -620.0
@export var gravity: float = 1500.0
@export var max_health: int = 100
@export var fire_rate: float = 0.11

var health: int
var _fire_cooldown: float = 0.0
var _facing: float = 1.0


func _ready() -> void:
	health = max_health
	collision_layer = 1
	collision_mask = 1

	var shape := RectangleShape2D.new()
	shape.size = Vector2(30.0, 62.0)
	var collision_shape := CollisionShape2D.new()
	collision_shape.shape = shape
	add_child(collision_shape)

	health_changed.emit(health, max_health)


func _physics_process(delta: float) -> void:
	var direction := _movement_direction()
	velocity.x = direction * move_speed

	if not is_on_floor():
		velocity.y += gravity * delta
	elif _wants_jump():
		velocity.y = jump_velocity

	_fire_cooldown = maxf(_fire_cooldown - delta, 0.0)
	if Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT) and _fire_cooldown <= 0.0:
		shoot_at(get_global_mouse_position())

	var aim_direction := global_position.direction_to(get_global_mouse_position())
	if absf(aim_direction.x) > 0.05:
		_facing = signf(aim_direction.x)

	move_and_slide()
	queue_redraw()


func shoot_at(target: Vector2) -> void:
	_fire_cooldown = fire_rate
	var muzzle := global_position + Vector2(28.0 * _facing, -10.0)
	var bullet := BulletScene.new()
	bullet.setup(muzzle, target, self)
	get_tree().current_scene.add_child(bullet)


func take_damage(amount: int, _hit_position: Vector2 = Vector2.ZERO) -> void:
	health = maxi(health - amount, 0)
	health_changed.emit(health, max_health)
	if health == 0:
		died.emit()
		set_physics_process(false)
		set_process(false)
		queue_redraw()


func _movement_direction() -> float:
	var direction := 0.0
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		direction -= 1.0
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		direction += 1.0
	return direction


func _wants_jump() -> bool:
	return Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP) or Input.is_key_pressed(KEY_SPACE)


func _draw() -> void:
	var body_color := Color(0.1, 0.75, 1.0) if health > 0 else Color(0.2, 0.25, 0.3)
	draw_rect(Rect2(Vector2(-15.0, -31.0), Vector2(30.0, 62.0)), body_color)
	draw_circle(Vector2(0.0, -43.0), 11.0, Color(0.85, 0.96, 1.0))
	draw_circle(Vector2(4.0 * _facing, -46.0), 2.0, Color(0.05, 0.08, 0.12))
	draw_line(Vector2(8.0 * _facing, -14.0), Vector2(34.0 * _facing, -10.0), Color(0.85, 0.9, 0.95), 6.0)
	draw_line(Vector2(22.0 * _facing, -10.0), Vector2(43.0 * _facing, -10.0), Color(0.2, 0.25, 0.32), 4.0)
