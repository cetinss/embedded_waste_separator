import RPi.GPIO as GPIO
import time
from RpiMotorLib import RpiMotorLib

# === GPIO Setup ===
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# === GPIO Pins ===
IR_PIN = 5           # IR sensor for object detection
METAL_PIN = 6        # Proximity sensor for metal detection
RAIN_PIN = 21        # Rain/moisture sensor for wet waste
BUZZER_PIN = 12      # Buzzer for feedback
SERVO_PIN = 13       # Servo motor for lid
STEPPER_PINS = [17, 18, 27, 22]  # Stepper motor input pins

# === GPIO Initialization ===
GPIO.setup(IR_PIN, GPIO.IN)
GPIO.setup(METAL_PIN, GPIO.IN)
GPIO.setup(RAIN_PIN, GPIO.IN)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# === Initialize Servo and Stepper Motors ===
servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(7)

stepper = RpiMotorLib.BYJMotor("StepperMotor", "28BYJ")

# === Fixed Bin Angles (degrees) ===
BIN_ANGLES = {
    "dry": 0,
    "wet": 120,
    "metal": 240
}

# === Initial Position ===
current_angle = 0  # Start at "dry" position

# === Buzzer Utility ===
def beep_buzzer(duration=0.5):
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

# === Lid Control ===
def open_and_close_lid():
    servo.ChangeDutyCycle(7)   # Open lid
    time.sleep(1)
    servo.ChangeDutyCycle(12)  # Close lid
    time.sleep(1)

# === Rotation Calculation ===
def calculate_rotation(current, target):
    """Determine shortest direction and angle to rotate"""
    clockwise = (target - current) % 360
    counter_clockwise = (current - target) % 360
    return (clockwise, True) if clockwise <= counter_clockwise else (counter_clockwise, False)

# === Degree to Step Conversion ===
def degrees_to_steps(degree):
    return int((degree / 360) * 512)

# === Main Loop ===
try:
    print("System started.")

    while True:
        if GPIO.input(IR_PIN) == 0:  # Object detected
            beep_buzzer(0.5)

            if GPIO.input(METAL_PIN) == 0:
                target_bin = "metal"
                print("Metal waste detected.")
            elif GPIO.input(RAIN_PIN) == 0:
                target_bin = "wet"
                print("Wet waste detected.")
            else:
                target_bin = "dry"
                print("Dry waste detected.")

            target_angle = BIN_ANGLES[target_bin]

            if target_angle != current_angle:
                degree_diff, direction = calculate_rotation(current_angle, target_angle)
                step_count = degrees_to_steps(degree_diff)

                print(f"{current_angle}° → {target_angle}° = {step_count} steps, direction: {'clockwise' if direction else 'counter-clockwise'}")

                stepper.motor_run(STEPPER_PINS, 0.001, step_count, direction, False, "half", 0.05)
                current_angle = target_angle  # Update current position

            else:
                print(f"Already at {target_bin} position. No rotation needed.")

            open_and_close_lid()

        time.sleep(0.5)

except KeyboardInterrupt:
    print("Program terminated.")
    GPIO.cleanup()
