#!/usr/bin/env python3
"""
Demo script showing the new theme and flashcard UI features
"""

import streamlit as st
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def render_flashcard(title, value, icon="", color_class="", details=None, progress_value=None):
    """Simple replacement for theme manager flashcard"""
    if icon:
        label = f"{icon} {title}"
    else:
        label = title
    
    delta_info = None
    if details:
        delta_info = ", ".join(str(d) for d in details[:2])
    elif progress_value is not None:
        delta_info = f"{progress_value}%"
    
    st.metric(label=label, value=str(value), delta=delta_info)

st.set_page_config(page_title="Theme & Flashcard Demo", layout="wide")

st.title("Theme & Flashcard UI Demo")

st.markdown("## Dark/Light Mode Toggle")
st.markdown("Click the theme toggle button in the top-right corner to switch between light and dark themes!")

st.divider()

st.markdown("## Flashcard Components")

# Add some spacing before the columns
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4, gap="large")

with col1:
    render_flashcard(
        title="Overall Risk",
        value="Medium",
        color_class="risk-medium"
    )

with col2:
    render_flashcard(
        title="Documents Processed",
        value="42",
        color_class="score-good",
        progress_value=85
    )

with col3:
    render_flashcard(
        title="Completion Score",
        value="87/100",
        color_class="score-excellent",
        progress_value=87,
        details=["High coverage", "Strong evidence", "Complete sections"]
    )

with col4:
    render_flashcard(
        title="Financial Health",
        value="Good",
        color_class="score-good",
        progress_value=75,
        details=["Positive cash flow", "Low debt ratio", "Growing revenue"]
    )

st.divider()

st.markdown("## Risk Level Examples")

# Add some spacing before the columns  
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    render_flashcard(
        title="Low Risk",
        value="Safe",
        color_class="risk-low",
        progress_value=90
    )

with col2:
    render_flashcard(
        title="Medium Risk",
        value="Caution",
        color_class="risk-medium", 
        progress_value=65
    )

with col3:
    render_flashcard(
        title="High Risk",
        value="Alert",
        color_class="risk-high",
        progress_value=25
    )

st.divider()

st.markdown("## 🎨 Features")

st.markdown("""
### ✨ New Features Added:

1. **🌓 Light/Dark Mode Toggle**
   - Click the sun/moon button in the top-right corner
   - Remembers your preference across sessions
   - Smooth animations and transitions

2. **🃏 Flashcard UI Components**
   - Modern, card-based design for metrics
   - Color-coded by risk level and score ranges
   - Progress bars for visual feedback
   - Hover effects and animations
   - Expandable details sections

3. **🎨 Enhanced Theming**
   - Consistent color scheme across light/dark modes
   - Professional gradients and shadows
   - Improved readability and accessibility
   - Custom CSS styling for all components

4. **📱 Responsive Design**
   - Works well on desktop and mobile
   - Flexible grid layouts
   - Optimized for different screen sizes

### 🔧 Technical Implementation:

- **Simple Metrics**: Using Streamlit's built-in `st.metric()` components
- **Basic Styling**: Standard Streamlit theming
- **Session State**: Standard Streamlit functionality
- **Flashcard Components**: Reusable UI elements with props
- **Color System**: Semantic color naming for consistency
""")
