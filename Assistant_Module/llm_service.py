import google.generativeai as genai
import os

def explain_cable_selection(calculation_data):
    """
    Calls the Gemini API to explain the reasoning for the cable selection, 
    strictly avoiding any recalculations or modifications to the numbers.
    """
    
    # We expect an API key to be set in environment variables
    # If not set, return a mock response or an error
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Dynamic fallback response if there is no API key configured
        initial_cable_size = calculation_data.get('initial_cable', {}).get('recommended_mm2', '--')
        cable_size = calculation_data.get('cable', {}).get('recommended_mm2', '--')
        v_status = calculation_data.get('voltage_drop_status', 'Unknown')
        adjusted = initial_cable_size != cable_size and initial_cable_size != '--'
        
        fallback_msg = (
            f"LLM Explanation is currently unavailable. Please ensure GEMINI_API_KEY "
            f"is set in your environment variables.\n\n"
            f"(Demo mode:\n"
        )
        
        if adjusted:
            fallback_msg += f"- Recommended Cable: The cable size was upgraded from {initial_cable_size} mm² to {cable_size} mm² to safely handle the current of {calculation_data.get('safe_current_a', 0):.2f} A and compensate for the voltage drop over distance.\n"
        else:
            fallback_msg += f"- Recommended Cable: The {cable_size} mm² cable was deterministically selected to safely handle your current of {calculation_data.get('safe_current_a', 0):.2f} A (which includes a 1.25 safety factor).\n"
            
        fallback_msg += f"- Voltage Drop Analysis: Your current voltage drop status is '{v_status}'. "
        
        if "WARNING" in v_status:
            fallback_msg += "Because the drop exceeds 5%, this will cause noticeable inefficiencies or potential equipment damage. You must consider increasing the cable thickness or reducing the distance."
        else:
            fallback_msg += "Your system operates within a safe and efficient voltage margin."
            
        fallback_msg += "\n\nNote: This is for guidance only and must be validated by a certified engineer.)"
        return fallback_msg

    genai.configure(api_key=api_key)
    
    # We will use gemini-flash-lite-latest as it is available and fast
    model = genai.GenerativeModel('gemini-flash-lite-latest')
    
    initial_cable_size = calculation_data.get('initial_cable', {}).get('recommended_mm2', '--')
    final_cable_size = calculation_data.get('cable', {}).get('recommended_mm2', '--')
    adjusted = initial_cable_size != final_cable_size and initial_cable_size != '--'
    
    prompt = f"""
You are an Intelligent Technical Assistant for an electrical engineering application (SpecSense AI).
Your role is to explain the reasoning behind a specific cable selection to the user based on the provided data.

### STRICT CONSTRAINTS:
1. DO NOT recalculate or modify any of the numbers provided in the Context Data.
2. Rely strictly on the Context Data provided below. 
3. Include a disclaimer that this is for guidance only and must be validated by a certified electrical engineer.
4. Keep the explanation concise, professional, and easy to understand.
5. Provide briefly any general safety recommendations or insights regarding this selection if applicable.

### CONTEXT DATA:
- Total Load: {calculation_data.get('total_power_w')} W
- Operating Current: {calculation_data.get('current_a'):.2f} A
- Safe Current (incl 1.25 margin): {calculation_data.get('safe_current_a'):.2f} A
- Initial Cable Size (Current-based): {initial_cable_size} mm²
- Final Recommended Cable Size: {final_cable_size} mm² (Max Capacity: {calculation_data.get('cable', {}).get('max_current')} A)
- Cable Material: {calculation_data.get('cable', {}).get('material')}
- Voltage Drop: {calculation_data.get('voltage_drop_v'):.2f} V ({calculation_data.get('voltage_drop_pct', 0):.2f}%)
- Voltage Drop Status: {calculation_data.get('voltage_drop_status')}
- Was Cable Upsized for Voltage Drop?: {"Yes" if adjusted else "No"}

### EXPLANATION REQUEST:
Explain why this final cable size ({final_cable_size} mm²) was selected.
If the cable was upsized from {initial_cable_size} mm² to {final_cable_size} mm², clearly explain that this was done specifically to compensate for excessive voltage drop over the distance, and explain how a larger cross-sectional area lowers resistance and improves system performance and safety.
VERY IMPORTANT: You MUST explicitly address the '{calculation_data.get('voltage_drop_status')}' Voltage Drop Status. If it's a WARNING, explain why a high voltage drop is dangerous and what the user should do (e.g. increase cable thickness or shorten distance).
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error connecting to LLM service: {str(e)}"

def explain_internal_wiring(wiring_data):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "LLM Explanation is currently unavailable. Please ensure GEMINI_API_KEY is set in your environment variables.\n\n(Demo mode: The system automatically divided your loads into discrete circuits based on standard current capacities. Sockets and lighting were split to avoid overloading standard MCBs (10A for lights, 16A for sockets). Cable sizes were selected to safely carry the current while maintaining a voltage drop ≤ 5% over the estimated routing lengths. MCBs were carefully sized to protect the cables from overheating.)"
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-lite-latest')
    
    num_circuits = len(wiring_data['circuits'])
    summary = wiring_data['summary']
    
    prompt = f"""
You are an Intelligent Technical Assistant for an electrical engineering application (SpecSense AI).
Your role is to explain the reasoning behind an internal wiring plan generated for an apartment.

### STRICT CONSTRAINTS:
1. DO NOT recalculate or modify any of the numbers provided in the Context Data.
2. Rely strictly on the Context Data provided below.
3. Include a disclaimer that this is for guidance only and must be validated by a certified electrical engineer.
4. Keep the explanation concise, professional, and easy to understand.
5. Explain briefly how circuit splitting (e.g., separating lights and sockets) improves safety.
6. Explain the concept of the Diversity Factor and why the Diversified Load is lower than the Raw Load.

### CONTEXT DATA:
- Number of Circuits Generated: {num_circuits}
- Total Raw Load: {summary['total_power_w']:.0f} W
- Total Diversified Load (Estimated real usage): {summary['total_power_diversified_w']:.0f} W
- Key Cable Distribution:
"""
    for size, length in summary['cable_totals'].items():
        if size != -1:
            prompt += f"  - {size} mm²: {length:.1f} meters\n"
            
    prompt += """
### EXPLANATION REQUEST:
Provide a brief summary of this wiring plan. Explain why the system assigned specific MCB ratings to protect specific cable sizes, and how diversity factors provide a more realistic estimate for the main panel sizing.
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error connecting to LLM service: {str(e)}"
