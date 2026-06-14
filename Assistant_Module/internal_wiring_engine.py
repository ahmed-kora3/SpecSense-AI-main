import math
from Assistant_Module.assistant_engine import CableSelectionEngine

class InternalWiringEngine:
    STANDARD_MCBS = [10, 16, 20, 25, 32, 40, 50, 63]

    @staticmethod
    def select_mcb(safe_current, cable_max_current):
        """
        Select the smallest standard MCB such that safe_current <= MCB <= cable_max_current.
        If none fits perfectly, return the closest safe size or fallback.
        """
        for mcb in InternalWiringEngine.STANDARD_MCBS:
            if mcb >= safe_current and mcb <= cable_max_current:
                return mcb
        # Fallback if no standard fits (e.g., load too high for largest cable, or gap)
        return None

    @staticmethod
    def split_into_circuits(item_count, w_per_item, voltage, max_circuit_current, prefix_name, base_length_per_item, room_bonus=0):
        circuits = []
        if item_count <= 0:
            return circuits
            
        total_w = item_count * w_per_item
        total_i = total_w / voltage
        safe_i = total_i * 1.25
        
        # How many circuits do we need?
        # We split based on safe_current vs max_circuit_current
        num_circuits = math.ceil(safe_i / max_circuit_current)
        if num_circuits == 0:
            num_circuits = 1
            
        items_per_circuit = math.ceil(item_count / num_circuits)
        
        items_allocated = 0
        circuit_idx = 1
        
        while items_allocated < item_count:
            items_this_circuit = min(items_per_circuit, item_count - items_allocated)
            c_power = items_this_circuit * w_per_item
            c_current = c_power / voltage
            c_safe_current = c_current * 1.25
            
            c_length = (items_this_circuit * base_length_per_item) + room_bonus
            
            circuits.append({
                'id': f"{prefix_name}-{circuit_idx}",
                'type': prefix_name,
                'power': c_power,
                'current': c_current,
                'safe_current': c_safe_current,
                'base_length': c_length,
                'items': items_this_circuit
            })
            
            items_allocated += items_this_circuit
            circuit_idx += 1
            
        return circuits

    @staticmethod
    def design_internal_wiring(inputs, heuristics, diversity, max_drop_pct=5.0):
        voltage = 220.0
        
        num_rooms = inputs.get('num_rooms', 0)
        num_acs = inputs.get('num_acs', 0)
        num_lights = inputs.get('num_lights', 0)
        num_sockets = inputs.get('num_sockets', 0)
        has_kitchen = inputs.get('has_kitchen', False)
        
        light_w = heuristics.get('light_w', 20)
        socket_w = heuristics.get('socket_w', 300)
        ac_w = heuristics.get('ac_w', 1500)
        kitchen_w = heuristics.get('kitchen_w', 3000)
        
        # Max currents for splitting
        # Lighting typically 10A max per circuit. We use 10A limits.
        max_light_current = 10.0 
        # Sockets typically 16A or 20A max. We'll use 16A for safety.
        max_socket_current = 16.0
        
        # 1. Distribute loads into circuits
        all_circuits = []
        
        # Lighting
        # Add room routing length for lighting base
        light_room_bonus = 0
        if num_lights > 0:
            light_room_bonus = (num_rooms * 12.0) / max(1, math.ceil(((num_lights*light_w/voltage)*1.25)/max_light_current))
        all_circuits.extend(InternalWiringEngine.split_into_circuits(num_lights, light_w, voltage, max_light_current, "Lighting", 2.0, light_room_bonus))
        
        # Sockets
        all_circuits.extend(InternalWiringEngine.split_into_circuits(num_sockets, socket_w, voltage, max_socket_current, "Sockets", 3.0, 0))
        
        # ACs (each gets its own circuit)
        for i in range(num_acs):
            c_power = ac_w
            c_current = c_power / voltage
            c_safe_current = c_current * 1.25
            c_length = 15.0 # base AC length
            all_circuits.append({
                'id': f"AC-{i+1}",
                'type': "AC",
                'power': c_power,
                'current': c_current,
                'safe_current': c_safe_current,
                'base_length': c_length,
                'items': 1
            })
            
        # Kitchen
        if has_kitchen:
            c_power = kitchen_w
            c_current = c_power / voltage
            c_safe_current = c_current * 1.25
            c_length = 10.0 # base kitchen length
            all_circuits.append({
                'id': "Kitchen-1",
                'type': "Kitchen",
                'power': c_power,
                'current': c_current,
                'safe_current': c_safe_current,
                'base_length': c_length,
                'items': 1
            })
            
        # 2. Design each circuit (Cable & MCB)
        selector = CableSelectionEngine()
        
        cable_totals = {}
        total_power_raw = 0
        total_power_diversified = 0
        
        final_circuits = []
        
        for c in all_circuits:
            # Length estimation: base + 2m drop + 10% routing
            est_length = (c['base_length'] + 2.0) * 1.10
            
            # Select cable (voltage drop aware)
            # We use 1 phase for internal circuits
            init_c, final_c, v_drop, v_drop_pct, v_status = selector.select_optimal_cable(
                c['safe_current'], voltage, est_length, 1, max_drop_pct
            )
            
            c_size = final_c['recommended_mm2'] if final_c else -1
            c_max_current = final_c['max_current'] if final_c else 0
            
            mcb = InternalWiringEngine.select_mcb(c['safe_current'], c_max_current)
            if not mcb:
                # If we couldn't find a standard MCB that fits perfectly, just round up safe_current
                mcb = math.ceil(c['safe_current'])
                
            c_details = {
                'id': c['id'],
                'type': c['type'],
                'power_w': c['power'],
                'current_a': c['current'],
                'safe_current_a': c['safe_current'],
                'length_m': est_length,
                'cable_size_mm2': c_size,
                'mcb_a': mcb,
                'voltage_drop_pct': v_drop_pct,
                'status': v_status
            }
            final_circuits.append(c_details)
            
            # Accumulate totals
            if c_size not in cable_totals:
                cable_totals[c_size] = 0
            cable_totals[c_size] += est_length
            
            total_power_raw += c['power']
            
            # Apply diversity factor based on type
            df = 1.0
            if c['type'] == 'Lighting':
                df = diversity.get('lighting_df', 0.8)
            elif c['type'] == 'Sockets':
                df = diversity.get('socket_df', 0.6)
            elif c['type'] == 'AC':
                df = diversity.get('ac_df', 0.9)
            elif c['type'] == 'Kitchen':
                df = diversity.get('kitchen_df', 0.8)
                
            total_power_diversified += (c['power'] * df)

        summary = {
            'total_power_w': total_power_raw,
            'total_power_diversified_w': total_power_diversified,
            'cable_totals': cable_totals
        }
        
        return {
            'circuits': final_circuits,
            'summary': summary
        }
