import logging
from time import sleep
from ptz_camera import PTZCamera
from ptz_camera_exceptions import CommandFailed, NetworkError, TimeoutError


def setup_logging():
    """Configure logging to see debug output."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def get_current_position(ptz: PTZCamera) -> tuple:
    """
    Get the current camera position.
    
    Args:
        ptz: PTZCamera instance
        
    Returns:
        Tuple of (zoom, pan, tilt)
    """
    cur_zoom = ptz.get_zoom()
    pan_tilt = ptz.get_pan_tilt_position()
    
    if pan_tilt is None:
        raise CommandFailed("get_pan_tilt_position", ptz.address)
    
    cur_pan, cur_tilt = pan_tilt
    return (cur_zoom, cur_pan, cur_tilt)


def map_presets(ptz: PTZCamera, max_preset: int = 5) -> dict:
    """
    Map preset positions to their preset numbers.
    
    Args:
        ptz: PTZCamera instance
        max_preset: Maximum preset number to check (default: 5)
        
    Returns:
        Dictionary mapping position tuples to preset numbers
    """
    preset_mapping = {}
    preset_min, preset_max = ptz.preset_bounds
    
    print("\nMapping presets...")
    print("-" * 60)
    
    # Limit to max_preset or the camera's maximum
    end_preset = min(max_preset, preset_max + 1)
    
    for preset_num in range(preset_min, end_preset):
        try:
            # Move to preset
            print(f"\nMoving to preset {preset_num}...", end=" ")
            ptz.move_to_preset(preset_num)
            
            # Wait for camera to reach position
            sleep(3)
            
            # Get position
            position = get_current_position(ptz)
            print(f"Position: {position}")
            
            # Store mapping
            preset_mapping[position] = preset_num
            
        except CommandFailed as e:
            print(f"Failed: {e}")
            continue
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    print("-" * 60)
    return preset_mapping


def restore_position(ptz: PTZCamera, zoom: int, pan: int, tilt: int) -> None:
    """
    Restore camera to a specific position.
    
    Args:
        ptz: PTZCamera instance
        zoom: Target zoom value
        pan: Target pan value
        tilt: Target tilt value
    """
    print(f"\nRestoring original position: zoom={zoom}, pan={pan}, tilt={tilt}")
    
    try:
        ptz.set_zoom(zoom)
        sleep(ptz.delay)
        
        ptz.set_pan_tilt_position(
            pan=pan,
            tilt=tilt,
            speed=20,
            select=0
        )
        sleep(2)
        
        print("Position restored successfully")
        
    except Exception as e:
        print(f"Error restoring position: {e}")


def find_current_preset(
    current_position: tuple,
    preset_mapping: dict,
    tolerance: int = 100
) -> str:
    """
    Find which preset matches the current position.
    
    Args:
        current_position: Tuple of (zoom, pan, tilt)
        preset_mapping: Dictionary mapping positions to preset numbers
        tolerance: Allowed difference for position matching (default: 100)
        
    Returns:
        String describing the current preset
    """
    # Try exact match first
    if current_position in preset_mapping:
        preset_num = preset_mapping[current_position]
        return f"{preset_num} (exact match)"
    
    # Try fuzzy match with tolerance
    cur_zoom, cur_pan, cur_tilt = current_position
    
    for (zoom, pan, tilt), preset_num in preset_mapping.items():
        if (abs(zoom - cur_zoom) <= tolerance and
            abs(pan - cur_pan) <= tolerance and
            abs(tilt - cur_tilt) <= tolerance):
            return f"{preset_num} (approximate match)"
    
    return "UNKNOWN"


def run():
    """Main function to map camera presets."""
    setup_logging()
    
    camera_ip = '192.168.0.10'
    
    print("=" * 60)
    print("PTZ Camera Preset Mapper")
    print("=" * 60)
    
    try:
        # Create camera instance with context manager for automatic cleanup
        with PTZCamera(
            address=camera_ip,
            timeout=10.0,  # Increased timeout for reliability
            retry_attempts=3
        ) as ptz:
            
            print(f"\nConnected to camera at {camera_ip}")
            print(f"Camera model: {ptz.camera}")
            print(f"Preset range: {ptz.preset_bounds}")
            
            # Get current position
            print("\nGetting current position...")
            original_position = get_current_position(ptz)
            cur_zoom, cur_pan, cur_tilt = original_position
            print(f"Current Position: zoom={cur_zoom}, pan={cur_pan}, tilt={cur_tilt}")
            
            # Map all presets (checking first 5)
            preset_mapping = map_presets(ptz, max_preset=5)
            
            # Display mapping results
            print("\nPreset Mapping Results:")
            print("-" * 60)
            if preset_mapping:
                for position, preset_num in sorted(preset_mapping.items(), 
                                                   key=lambda x: x[1]):
                    zoom, pan, tilt = position
                    print(f"  Preset {preset_num}: zoom={zoom}, pan={pan}, tilt={tilt}")
            else:
                print("  No presets mapped successfully")
            print("-" * 60)
            
            # Restore original position
            restore_position(ptz, cur_zoom, cur_pan, cur_tilt)
            
            # Wait for position to stabilize
            sleep(2)
            
            # Check final position
            final_position = get_current_position(ptz)
            current_preset = find_current_preset(final_position, preset_mapping)
            
            print(f"\nCamera is currently on preset: {current_preset}")
            
            # Summary
            print("\n" + "=" * 60)
            print("Summary:")
            print(f"  Total presets checked: 5")
            print(f"  Successfully mapped: {len(preset_mapping)}")
            print(f"  Current preset: {current_preset}")
            print("=" * 60)
    
    except NetworkError as e:
        print(f"\nNetwork Error: {e}")
        print("Check that the camera is powered on and reachable on the network.")
    
    except TimeoutError as e:
        print(f"\nTimeout Error: {e}")
        print("Camera is not responding. It may be busy or offline.")
    
    except CommandFailed as e:
        print(f"\nCommand Failed: {e}")
        print("The camera rejected a command. Check camera state.")
    
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run()
