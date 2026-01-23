import logging
from time import sleep
from ptz_camera import PTZCamera
from ptz_camera_exceptions import CommandFailed, NetworkError, TimeoutError


def setup_logging():
    """Configure logging for test output."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def wait_for_power_transition(cam: PTZCamera, timeout: int = 10) -> bool:
    """
    Wait for camera to finish power state transition.
    
    Args:
        cam: PTZCamera instance
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if transition completed, False if timed out
    """
    elapsed = 0
    while elapsed < timeout:
        state = cam.get_power_state()
        if state != "Transitioning":
            return True
        sleep(0.5)
        elapsed += 0.5
    return False


def test_power_control(cam: PTZCamera) -> None:
    """Test power on/off functionality."""
    print("\n" + "="*60)
    print("Testing Power Control")
    print("="*60)
    
    current_state = cam.get_power_state()
    print(f"Current power state: {current_state}")
    
    if current_state != "On":
        print("Powering on camera...")
        cam.set_power_state(True)
        
        if wait_for_power_transition(cam, timeout=10):
            print(f"Camera powered on: {cam.get_power_state()}")
            sleep(4)  # Additional stabilization time
        else:
            print("Warning: Camera still transitioning after timeout")


def test_presets(cam: PTZCamera, presets: list = None) -> None:
    """
    Test moving to preset positions.
    
    Args:
        cam: PTZCamera instance
        presets: List of preset numbers to test (default: 0-4)
    """
    print("\n" + "="*60)
    print("Testing Preset Positions")
    print("="*60)
    
    if presets is None:
        presets = [0, 1, 2, 3, 4]
    
    for preset_num in presets:
        print(f"\nMoving to preset {preset_num}...", end=" ")
        try:
            cam.move_to_preset(preset_num)
            sleep(4)  # Wait for movement to complete
            position = cam.get_pan_tilt_position()
            if position:
                print(f"Position: {position}")
            else:
                print("Position query failed")
        except CommandFailed as e:
            print(f"Failed: {e}")


def test_pan_tilt_positions(cam: PTZCamera) -> None:
    """Test various pan/tilt positions in a pattern."""
    print("\n" + "="*60)
    print("Testing Pan/Tilt Positions")
    print("="*60)
    
    # Get valid ranges
    pan_min, pan_max = cam.pan_bounds
    tilt_min, tilt_max = cam.tilt_bounds
    
    # Calculate center position
    center_pan = (pan_min + pan_max) // 2
    center_tilt = (tilt_min + tilt_max) // 2
    
    print(f"\nPan range: {pan_min} to {pan_max}")
    print(f"Tilt range: {tilt_min} to {tilt_max}")
    print(f"Center position: pan={center_pan}, tilt={center_tilt}")
    
    # Define test positions: (pan, tilt, description)
    test_positions = [
        (center_pan, center_tilt, "Center"),
        (center_pan, tilt_max, "Center-Top"),
        (center_pan, center_tilt, "Center"),
        (center_pan, tilt_min, "Center-Bottom"),
        (center_pan, center_tilt, "Center"),
        (pan_max, center_tilt, "Right-Center"),
        (center_pan, center_tilt, "Center"),
        (pan_min, center_tilt, "Left-Center"),
        (center_pan, center_tilt, "Center (return)"),
    ]
    
    for pan, tilt, description in test_positions:
        print(f"\n{description}: pan={pan}, tilt={tilt}")
        try:
            cam.set_pan_tilt_position(
                pan=pan,
                tilt=tilt,
                speed=20,
                select=0
            )
            sleep(2)
            
            # Verify position
            actual_pos = cam.get_pan_tilt_position()
            if actual_pos:
                actual_pan, actual_tilt = actual_pos
                print(f"  Actual: pan={actual_pan}, tilt={actual_tilt}")
                
                # Check if close to target
                pan_diff = abs(actual_pan - pan)
                tilt_diff = abs(actual_tilt - tilt)
                if pan_diff < 500 and tilt_diff < 500:
                    print(f"    Position accurate (diff: pan={pan_diff}, tilt={tilt_diff})")
                else:
                    print(f"    Position differs (diff: pan={pan_diff}, tilt={tilt_diff})")
            else:
                print("  Position query failed")
                
        except CommandFailed as e:
            print(f"  Failed: {e}")


def test_zoom_levels(cam: PTZCamera) -> None:
    """Test different zoom levels."""
    print("\n" + "="*60)
    print("Testing Zoom Levels")
    print("="*60)
    
    zoom_min, zoom_max = cam.zoom_bounds
    zoom_mid = (zoom_min + zoom_max) // 2
    
    print(f"Zoom range: {zoom_min} to {zoom_max}")
    
    # Test zoom levels: (value, description)
    zoom_levels = [
        (zoom_max, "Maximum zoom"),
        (zoom_mid, "Mid zoom"),
        (zoom_min, "Minimum zoom"),
    ]
    
    for zoom_value, description in zoom_levels:
        print(f"\n{description}: {zoom_value}")
        try:
            cam.set_zoom(zoom_value)
            sleep(2)
            
            # Verify zoom
            actual_zoom = cam.get_zoom()
            if actual_zoom:
                print(f"  Actual zoom: {actual_zoom}")
                diff = abs(actual_zoom - zoom_value)
                if diff < 50:
                    print(f"    Zoom accurate (diff: {diff})")
                else:
                    print(f"    Zoom differs (diff: {diff})")
            else:
                print("  Zoom query failed")
                
        except CommandFailed as e:
            print(f"  Failed: {e}")


def test_power_off(cam: PTZCamera) -> None:
    """Power off the camera."""
    print("\n" + "="*60)
    print("Powering Off Camera")
    print("="*60)
    
    try:
        cam.set_power_state(False)
        sleep(2)
        final_state = cam.get_power_state()
        print(f"Final power state: {final_state}")
    except CommandFailed as e:
        print(f"Power off failed: {e}")


def run_tests():
    """Run all camera tests."""
    setup_logging()
    
    camera_ip = "192.168.0.10"
    
    print("="*60)
    print("PTZ Camera Test Suite")
    print("="*60)
    print(f"Camera IP: {camera_ip}")
    
    try:
        with PTZCamera(
            address=camera_ip,
            timeout=10.0,
            retry_attempts=3
        ) as cam:
            
            print(f"Camera model: {cam.camera}")
            
            # Run test sequence
            test_power_control(cam)
            test_presets(cam)
            test_pan_tilt_positions(cam)
            test_zoom_levels(cam)
            test_power_off(cam)
            
            print("\n" + "="*60)
            print("All Tests Completed Successfully!")
            print("="*60)
    
    except NetworkError as e:
        print(f"\nNetwork Error: {e}")
        print("Check that the camera is powered on and reachable.")
    
    except TimeoutError as e:
        print(f"\nTimeout Error: {e}")
        print("Camera is not responding within the timeout period.")
    
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_tests()