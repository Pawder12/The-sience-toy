extends Area2D
class_name Bullet

@export var speed: float = 950.0
@export var damage: int = 25
@export var life_time: float = 1.4

var direction: Vector2 = Vector2.RIGHT
var shooter: Node


func setup(origin: Vector2, target: Vector2, shooter_node: Node) -> void:
	global_position = origin
	direction = origin.direction_to(target)
	if direction == Vector2.ZERO:
		direction = Vector2.RIGHT
	shooter = shooter_node


func _ready() -> void:
	collision_layer = 4
	collision_mask = 1 | 2
	body_entered.connect(_on_body_entered)

	var shape := CircleShape2D.new()
	shape.radius = 4.0
	var collision_shape := CollisionShape2D.new()
	collision_shape.shape = shape
	add_child(collision_shape)


func _process(delta: float) -> void:
	global_position += direction * speed * delta
	life_time -= delta
	if life_time <= 0.0:
		queue_free()
	queue_redraw()


func _draw() -> void:
	draw_circle(Vector2.ZERO, 4.0, Color(0.3, 0.95, 1.0))
	draw_line(-direction * 10.0, Vector2.ZERO, Color(0.8, 1.0, 1.0), 2.0)


func _on_body_entered(body: Node) -> void:
	if body == shooter:
		return

	if body.has_method("take_damage"):
		body.take_damage(damage, global_position)
		queue_free()
	elif body is StaticBody2D:
		queue_free()
