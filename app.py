import streamlit as st
import json
import os
import hashlib
import requests

# File paths
USER_DATA_FILE = "user_data.json"
LANGUAGE_DATA_FILE = "language_data.json"
LANGUAGE_DATABASE_FILE = "language_database.json"  # New file

# API URL
API_URL = "http://172.20.10.8:5000"

# Function to load translations from the database file
def load_translations():
    if os.path.exists(LANGUAGE_DATABASE_FILE):
        try:
            with open(LANGUAGE_DATABASE_FILE, "r", encoding="utf-8") as f:  # Explicit UTF-8
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, UnicodeDecodeError):
            st.error("Failed to load or decode language database file. Check format and encoding.")
            return {}
    return {}

# Load language database when app initializes
TRANSLATIONS = load_translations()


# Function to load user data
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except json.JSONDecodeError:
            pass
    return {}

# Function to save user data
def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f)

# Function to load language data
def load_language_data():
    if os.path.exists(LANGUAGE_DATA_FILE):
        try:
            with open(LANGUAGE_DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}

# Function to save language data
def save_language_data(data):
    with open(LANGUAGE_DATA_FILE, "w") as f:
        json.dump(data, f)

# Function to hash the password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "email" not in st.session_state:
    st.session_state.email = ""
if "first_visit" not in st.session_state:
    st.session_state.first_visit = True
if "show_modal" not in st.session_state:
    st.session_state.show_modal = True
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "show_login_form" not in st.session_state:
    st.session_state.show_login_form = False
if "tracking_enabled" not in st.session_state:
    st.session_state.tracking_enabled = False
if "language" not in st.session_state:
    st.session_state.language = "en"  # Default language


# Load user data
user_data = load_user_data()
# Load language data
language_data = load_language_data()


# Auto-login if data exists for this device
if user_data.get("logged_in"):
    st.session_state.logged_in = True
    st.session_state.user_name = user_data.get("name", "")
    st.session_state.email = user_data.get("email", "")
    st.session_state.first_visit = False
    st.session_state.show_modal = False

# Load language preference from language data
if "language" in language_data:
     st.session_state.language = language_data["language"]


# Function to translate text
def translate_text(key):
    return TRANSLATIONS.get(st.session_state.language, {}).get(key, key)


# Set page configuration
st.set_page_config(page_title=translate_text("title"), layout="wide")

# Custom CSS to hide the top right menu and the Manage app button, and the footer and the Streamlit icon at the bottom
st.markdown(
    """
    <style>
        [data-testid="stToolbar"] {
          display: none;
        }
       [data-testid="stAppViewContainer"] > div:nth-child(2){
          display: none;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stDecoration"]{visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)



# Custom CSS to make buttons scrollable and logo in corner
st.markdown(
    """
    <style>
    [data-testid="stSidebar"]{
      overflow-y: auto; /* Make it scrollable */
       height: 100vh;

    }
     /* Logo styles */
    [data-testid="stSidebar"] h1{
       padding-left: 5px;/*move text to left with 5 pixels margin*/
       text-align: left; 

    }
     /* Add custom scrollbar styling */
    [data-testid="stSidebar"]::-webkit-scrollbar {
        width: 8px;
    }
    [data-testid="stSidebar"]::-webkit-scrollbar-thumb {
        background-color: #888; /* Darker scrollbar */
        border-radius: 8px;
    }
    [data-testid="stSidebar"]::-webkit-scrollbar-thumb:hover {
        background-color: #555; /* Hover effect for scrollbar */
    }


    </style>
    """,
    unsafe_allow_html=True,
)


# Modal Logic (Sign-Up/Login)
if st.session_state.show_modal:
    with st.container():
        st.markdown(
            f'<div id="myModal" class="modal" style="display:block;"><div class="modal-content"><span class="close" id="closeModal">×</span>',
            unsafe_allow_html=True,
        )

        if not st.session_state.show_login_form:
            st.title(translate_text("signup_title"))
            st.subheader(translate_text("signup_subtitle"))
            name = st.text_input(translate_text("enter_name"))
            email = st.text_input(translate_text("enter_email"))
            password = st.text_input(translate_text("enter_password"), type="password")

            if st.button(translate_text("signup")):
                if name and email and password:
                    if email not in [
                        user_info.get("email")
                        for user_info in user_data.values()
                        if isinstance(user_info, dict)
                    ]:
                        hashed_password = hash_password(password)
                        user_data[name] = {
                            "password": hashed_password,
                            "email": email,
                            "logged_in": True,
                        }
                        st.session_state.logged_in = True
                        st.session_state.user_name = name
                        st.session_state.email = email
                        st.session_state.show_modal = False
                        user_data.update({"logged_in": True, "name": name, "email": email})
                        #save language in language data json
                        language_data.update({"language":st.session_state.language})
                        save_language_data(language_data)
                        save_user_data(user_data)
                        st.rerun()
                    else:
                        st.warning(translate_text("account_exists"))
                else:
                    st.warning(translate_text("fill_fields"))
            if st.button(translate_text("switch_login"), key="showLoginButton"):
                st.session_state.show_login_form = True
                st.rerun()
        else:
            st.title(translate_text("login_title"))
            st.subheader(translate_text("login_subtitle"))
            email = st.text_input(translate_text("enter_email"))
            password = st.text_input(translate_text("enter_password"), type="password")

            if st.button(translate_text("login")):
                hashed_password = hash_password(password)
                for name, user_info in user_data.items():
                   if isinstance(user_info,dict) and user_info.get('email')==email and  user_info.get('password') == hashed_password:
                       st.session_state.logged_in = True
                       st.session_state.user_name = name
                       st.session_state.email = email
                       st.session_state.show_modal = False
                       #save language in language data json
                       language_data.update({"language":st.session_state.language})
                       save_language_data(language_data)
                       st.rerun()
                       break
                else:
                    st.warning(
                        translate_text("invalid_credentials")
                    )

            if st.button(translate_text("switch_signup"), key="showSignUpButton"):
                st.session_state.show_login_form = False
                st.rerun()

        st.markdown("</div></div>", unsafe_allow_html=True)

    # JavaScript to control modal visibility
    st.markdown(
        """
        <script>
        var modal = document.getElementById("myModal");
        var closeBtn = document.getElementById("closeModal");

        if(closeBtn){
            closeBtn.onclick = function() {
                modal.style.display = "none";
            };

            window.onclick = function(event) {
                if (event.target == modal) {
                    modal.style.display = "none";
                }
            };
        }
        </script>
        """,
        unsafe_allow_html=True,
    )

# Function to make API calls
def make_api_call(endpoint, method="POST"):
    try:
        url = f"{API_URL}{endpoint}"
        if method == "POST":
            response = requests.post(url)
        elif method == "GET":
            response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None

# Sidebar navigation section
with st.sidebar:
     st.title(translate_text("title"))

     for i in range(1, 5):
         st.sidebar.write(f"  ")

    #Button links
     if st.sidebar.button(translate_text("home"), key="home", use_container_width=True):
         st.session_state.current_page = "home"
     if st.sidebar.button(translate_text("study"), key="study", use_container_width=True):
         st.session_state.current_page = "study"
     if st.sidebar.button(translate_text("profile"), key="profile", use_container_width=True):
          st.session_state.current_page = "profile"
     if st.sidebar.button(translate_text("call_help"), key="call_help", use_container_width=True):
         st.session_state.current_page = "call_help"

     for i in range(1, 20):
         st.sidebar.write(f"  ")

# Main content based on navigation
if st.session_state.logged_in:
    if st.session_state.current_page == "home":
        st.title(translate_text("title"))
        st.subheader(translate_text("welcome_dashboard"))

        # Advanced Mathematics Progress
        st.subheader(translate_text("advanced_math"))
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(0.65)  # Progress bar at 65%
            st.text(translate_text("last_activity")+ "q Calculus II - Integration")
            st.text(translate_text("time_left") + "2h 30m")
        with col2:
            st.button(translate_text("continue_learning"), use_container_width=True)

        # Areas of Excellence
        st.subheader(translate_text("areas_excellence"))
        col3, col4 = st.columns(2)
        with col3:
            st.write(f"### {translate_text('programming')}")
            st.success(f"95% - {translate_text('top_performer')}")
            st.write(f"### {translate_text('physics')}")
            st.success(f"92% - {translate_text('perfect_lab')}")
            st.write(f"### {translate_text('statistics')}")
            st.success(f"90% - {translate_text('advanced_problem')}")

        # Subject Progress
        st.subheader(translate_text("subject_progress"))
        col5, col6, col7 = st.columns(3)
        with col5:
            st.metric(translate_text("geometry"), "65%", delta=translate_text("practice_more"))
        with col6:
            st.metric(translate_text("chemistry"), "70%", delta=translate_text("review_table"))
        with col7:
            st.metric(translate_text("literature"), "68%", delta=translate_text("focus_analysis"))

        # Tracking Control
        st.subheader(translate_text("iris_tracking"))
        col8, col9 = st.columns(2)
        with col8:
            if st.button(
                translate_text("turn_on") if not st.session_state.tracking_enabled else translate_text("turn_off"),
                use_container_width=True,
            ):
                if not st.session_state.tracking_enabled:
                    response = make_api_call("/start")
                    if response and response.get("message") == "Tracking started":
                        st.session_state.tracking_enabled = True
                        st.success(translate_text("tracking_is_on"))
                    else:
                        st.error(translate_text("failed_start"))
                else:
                    response = make_api_call("/stop")
                    if response and response.get("message") == "Tracking stopped":
                        st.session_state.tracking_enabled = False
                        st.success(translate_text("tracking_is_off"))
                    else:
                        st.error(translate_text("failed_stop"))
                st.rerun()
        with col9:
            status_response = make_api_call("/status", method="GET")
            if status_response:
                tracking_status = status_response.get("tracking_enabled", False)
                st.write(f"**{translate_text('tracking_status')}** {'ON' if tracking_status else 'OFF'}")
            else:
                st.write(f"**{translate_text('tracking_status')}** {translate_text('unknown_status')}")

    elif st.session_state.current_page == "study":
        st.title(translate_text("study_section_title"))
        st.write(translate_text("study_section_message"))

        # Study buttons with descriptions
        st.button(translate_text("mathematics"), use_container_width=True)
        st.button(translate_text("science"), use_container_width=True)
        st.button(translate_text("english"), use_container_width=True)
        st.button(translate_text("social_science"), use_container_width=True)
        st.button(translate_text("computer"), use_container_width=True)
        for i in range(1, 17):
            st.write(f"  ")


    elif st.session_state.current_page == "profile":
        st.title(translate_text("profile_section"))
        if st.session_state.logged_in:
            st.write(f"**{translate_text('name')}** {st.session_state.user_name}")
            st.write(f"**{translate_text('email')}** {st.session_state.email}")

            # Language selection dropdown
            selected_language = st.selectbox("Select Language", options=list(TRANSLATIONS.keys()), index=list(TRANSLATIONS.keys()).index(st.session_state.language) )
            if selected_language != st.session_state.language:
               st.session_state.language = selected_language
                #save language in language data json
               language_data.update({"language":st.session_state.language})
               save_language_data(language_data)
               st.rerun()


            if st.button(translate_text("logout")):
                # Reset the session state
                st.session_state.logged_in = False
                st.session_state.user_name = ""
                st.session_state.email = ""
                st.session_state.show_modal = True
                st.session_state.show_login_form = False

                # Update user data to reflect logout
                user_data.update({"logged_in": False})
                save_user_data(user_data)
                st.rerun()


    elif st.session_state.current_page == "call_help":
        st.title(translate_text("call_help_title"))
        st.write(translate_text("call_help_message"))
else:
    st.write("Please log in to access the dashboard.")
