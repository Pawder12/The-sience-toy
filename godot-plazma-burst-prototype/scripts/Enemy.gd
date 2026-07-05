extends CharacterBody2D
class_name Enemy

signal died(enemy: Enemy)

const BulletScene = preload("res://scripts/Bullet.gd")

@export var move_speed: float = 170.0
@export var gravity: float = 1500.0
@export var max_health: int = 60
@export var detection_range: float = 760.0
@export var fire_range: float = 620.0
@export var fire_rate: float = 0.75

var target: Player
var health: int
var _fire_cooldown: float = 0.0
var _facing: float = -1.0


func setup(player: Player) -> void:
	target = player


func _ready() -> void:
	health = max_health
	collision_layer = 2
	collision_mask = 1

	var shape := RectangleShape2D.new()
	shape.size = Vector2(30.0, 58.0)
	var collision_shape := CollisionShape2D.new()
	collision_shape.shape = shape
	add_child(collision_shape)


func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y += gravity * delta

	_fire_cooldown = maxf(_fire_cooldown - delta, 0.0)

	if is_instance_valid(target):
		var offset := target.global_position - global_position
		var distance := offset.length()
		if distance <= detection_range:
			if absf(offset.x) > 110.0:
				velocity.x = signf(offset.x) * move_speed
			else:
				velocity.x = move_toward(velocity.x, 0.0, move_speed * delta * 6.0)

			if absf(offset.x) > 0.05:
				_facing = signf(offset.x)
			if distance <= fire_range and _fire_cooldown <= 0.0:
				_shoot_at(target.global_position + Vector2(0.0, -10.0))
		else:
			velocity.x = move_toward(velocity.x, 0.0, move_speed * delta * 2.0)

	move_and_slide()
	queue_redraw()


func take_damage(amount: int, _hit_position: Vector2 = Vector2.ZERO) -> void:
	health = maxi(health - amount, 0)
	if health == 0:
		died.emit(self)
		queue_free()
	queue_redraw()


func _shoot_at(target_position: Vector2) -> void:
	_fire_cooldown = fire_rate
	var muzzle := global_position + Vector2(24.0 * _facing, -8.0)
	var bullet := BulletScene.new()
	bullet.setup(muzzle, target_position, self)
	get_tree().current_scene.add_child(bullet)


func _draw() -> void:
	draw_rect(Rect2(Vector2(-15.0, -29.0), Vector2(30.0, 58.0)), Color(0.95, 0.24, 0.2))
	draw_circle(Vector2(0.0, -40.0), 10.0, Color(1.0, 0.74, 0.58))
	draw_circle(Vector2(4.0 * _facing, -42.0), 2.0, Color(0.1, 0.03, 0.02))
	draw_line(Vector2(8.0 * _facing, -12.0), Vector2(32.0 * _facing, -8.0), Color(0.15, 0.1, 0.1), 5.0)

	var health_ratio := float(health) / float(max_health)
	draw_rect(Rect2(Vector2(-18.0, -58.0), Vector2(36.0, 4.0)), Color(0.25, 0.05, 0.04))
	draw_rect(Rect2(Vector2(-18.0, -58.0), Vector2(36.0 * health_ratio, 4.0)), Color(1.0, 0.35, 0.25))
