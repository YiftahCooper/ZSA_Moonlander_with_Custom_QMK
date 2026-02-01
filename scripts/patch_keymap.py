#!/usr/bin/env python3
import sys
import re

def patch_keymap(filepath):
    """Patch Oryx-generated keymap.c with custom Double Tap Space logic."""
    
    with open(filepath, 'r') as f:
        content = f.read()

    # Define our custom dance name
    DANCE_NAME = "DANCE_5"
    
    # Step 1: Add to tap_dance_codes enum if not already present
    if DANCE_NAME not in content:
        # Find the enum and add our entry before the closing brace
        enum_pattern = r'(enum tap_dance_codes \{[^}]*)(\};)'
        match = re.search(enum_pattern, content, re.DOTALL)
        if match:
            # Check if there's already a trailing comma before the closing brace
            enum_body = match.group(1)
            if not enum_body.rstrip().endswith(','):
                replacement = match.group(1) + ',\n  ' + DANCE_NAME + match.group(2)
            else:
                replacement = match.group(1) + '\n  ' + DANCE_NAME + ',' + match.group(2)
            content = content.replace(match.group(0), replacement)
            print(f"✓ Added {DANCE_NAME} to tap_dance_codes enum")

    # Step 2: Update dance_state array size
    # Find "static tap dance_state[N];" and increment N
    state_pattern = r'static tap dance_state\[(\d+)\];'
    match = re.search(state_pattern, content)
    if match:
        current_size = int(match.group(1))
        new_size = max(current_size, 6)  # Ensure at least 6
        content = re.sub(state_pattern, f'static tap dance_state[{new_size}];', content)
        print(f"✓ Updated dance_state array to size {new_size}")

    # Step 3: Inject custom dance functions before tap_dance_actions
    custom_functions = '''
void on_dance_5(tap_dance_state_t *state, void *user_data);
void dance_5_finished(tap_dance_state_t *state, void *user_data);
void dance_5_reset(tap_dance_state_t *state, void *user_data);

void on_dance_5(tap_dance_state_t *state, void *user_data) {
    // No intermediate action needed
}

void dance_5_finished(tap_dance_state_t *state, void *user_data) {
    dance_state[5].step = dance_step(state);
    switch (dance_state[5].step) {
        case SINGLE_TAP: register_code16(KC_SPACE); break;
        case SINGLE_HOLD: register_code16(KC_SPACE); break;
        case DOUBLE_TAP: 
            tap_code16(KC_DOT);
            tap_code16(KC_SPACE);
            break;
        case DOUBLE_SINGLE_TAP: tap_code16(KC_SPACE); register_code16(KC_SPACE); break;
    }
}

void dance_5_reset(tap_dance_state_t *state, void *user_data) {
    wait_ms(10);
    switch (dance_state[5].step) {
        case SINGLE_TAP: unregister_code16(KC_SPACE); break;
        case SINGLE_HOLD: unregister_code16(KC_SPACE); break;
        case DOUBLE_SINGLE_TAP: unregister_code16(KC_SPACE); break;
    }
    dance_state[5].step = 0;
}

'''

    # Insert before tap_dance_actions if not already present
    if 'void on_dance_5' not in content:
        actions_marker = 'tap_dance_action_t tap_dance_actions[] = {'
        if actions_marker in content:
            content = content.replace(actions_marker, custom_functions + actions_marker)
            print("✓ Injected dance_5 functions")

    # Step 4: Add to tap_dance_actions array
    action_entry = f'[{DANCE_NAME}] = ACTION_TAP_DANCE_FN_ADVANCED(on_dance_5, dance_5_finished, dance_5_reset),'
    
    if action_entry not in content:
        # Find the closing of tap_dance_actions
        actions_pattern = r'(tap_dance_action_t tap_dance_actions\[\] = \{[^}]*)(\};)'
        match = re.search(actions_pattern, content, re.DOTALL)
        if match:
            # Add before closing brace
            actions_body = match.group(1)
            if not actions_body.rstrip().endswith(','):
                replacement = actions_body + ',\n        ' + action_entry + '\n' + match.group(2)
            else:
                replacement = actions_body + '\n        ' + action_entry + '\n' + match.group(2)
            content = content.replace(match.group(0), replacement)
            print("✓ Added dance_5 to tap_dance_actions")

    # Step 5: Replace KC_SPACE with TD(DANCE_5) in Layer 0
    # Find the last occurrence of KC_SPACE in layer 0 definition
    layer0_pattern = r'(\[0\] = LAYOUT_moonlander\([^)]*\))'
    layer0_match = re.search(layer0_pattern, content, re.DOTALL)
    
    if layer0_match:
        layer0_content = layer0_match.group(1)
        # Replace the LAST KC_SPACE (which is the right thumb space key)
        # We use rsplit to find the last occurrence
        if 'KC_SPACE' in layer0_content:
            # Split from the right, replace first occurrence, rejoin
            parts = layer0_content.rsplit('KC_SPACE', 1)
            new_layer0 = f'TD({DANCE_NAME})'.join(parts)
            content = content.replace(layer0_match.group(0), new_layer0)
            print("✓ Replaced Space key with TD(DANCE_5) in Layer 0")

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"\n✅ Patching complete: {filepath}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 patch_keymap.py <path_to_keymap.c>")
        sys.exit(1)
    
    patch_keymap(sys.argv[1])
