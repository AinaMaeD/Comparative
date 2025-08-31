import simpy
import random
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

# -------------------------------
# DISCRETE EVENT SIMULATION (DES)
# -------------------------------
def student(env, name, counter, service_time, wait_times):
    arrival = env.now
    with counter.request() as req:
        yield req
        wait = env.now - arrival
        wait_times.append(wait)
        yield env.timeout(random.expovariate(1.0 / service_time))

def run_discrete(num_students, arrival_rate, service_time, servers):
    env = simpy.Environment()
    counter = simpy.Resource(env, capacity=servers)
    wait_times = []

    def arrival_process(env, counter):
        for i in range(num_students):
            yield env.timeout(random.expovariate(1.0 / arrival_rate))
            env.process(student(env, f"Student {i}", counter, service_time, wait_times))

    env.process(arrival_process(env, counter))
    env.run()
    return wait_times

# -------------------------------
# CONTINUOUS SIMULATION (CS)
# -------------------------------
def run_continuous(total_time, dt, inflow_rate, service_rate):
    times = np.arange(0, total_time, dt)
    queue = [0]

    for t in times[1:]:
        dq = inflow_rate - service_rate * queue[-1]
        queue.append(max(queue[-1] + dq * dt, 0))
    return times, queue

# -------------------------------
# CUSTOM STYLE
# -------------------------------
page_bg = """
<style>
/* Background gradient */
.stApp {
    background: linear-gradient(135deg, #E0F7FA, #E1BEE7);
    color: #000000;
}

/* Title */
h1 {
    text-align: center;
    color: #4A148C;
}

/* Subheaders */
h2, h3 {
    color: #006064;
}

/* Cards */
div[data-testid="stVerticalBlock"] > div {
    background: rgba(255,255,255,0.8);
    padding: 15px 20px;
    margin: 10px 0px;
    border-radius: 15px;
    box-shadow: 2px 2px 12px rgba(0,0,0,0.1);
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# -------------------------------
# STREAMLIT APP (Prototype)
# -------------------------------
st.title("🏫 CSPC Registrar Office – Student Flow Simulation")
st.markdown("""
This prototype demonstrates the **Comparative Analysis of Discrete Event Simulation (DES)**  
and **Continuous Simulation (CS)** for optimizing student flow at the **Registrar’s Office, CSPC**.
""")

# Parameters (user input)
st.sidebar.header("⚙️ Simulation Settings")
num_students = st.sidebar.slider("Number of Students", 50, 500, 200, step=50)
arrival_rate = st.sidebar.slider("Average Arrival Interval (minutes)", 1, 10, 4)
service_time = st.sidebar.slider("Average Service Time (minutes)", 1, 10, 5)
servers = st.sidebar.slider("Number of Service Counters", 1, 5, 2)
total_time = st.sidebar.slider("Simulation Time (Continuous)", 50, 200, 100)

# Run simulations
des_wait_times = run_discrete(num_students, arrival_rate, service_time, servers)
times, queue = run_continuous(total_time, 1, 1/arrival_rate, 1/service_time)

# Display results
col1, col2 = st.columns(2)

with col1:
    st.subheader("📌 Discrete Event Simulation (Registrar Office)")
    st.write(f"**Average Waiting Time:** {np.mean(des_wait_times):.2f} minutes")
    st.write(f"**Maximum Waiting Time:** {np.max(des_wait_times):.2f} minutes")
    fig, ax = plt.subplots()
    ax.hist(des_wait_times, bins=20, color="skyblue", edgecolor="black")
    ax.set_title("Waiting Time Distribution (DES)")
    ax.set_xlabel("Wait Time (minutes)")
    ax.set_ylabel("Number of Students")
    st.pyplot(fig)

with col2:
    st.subheader("📌 Continuous Simulation (Registrar Office)")
    st.write(f"**Final Queue Length:** {queue[-1]:.2f} students")
    st.write(f"**Average Queue Length:** {np.mean(queue):.2f} students")
    fig, ax = plt.subplots()
    ax.plot(times, queue, color="orange")
    ax.set_title("Queue Length Over Time (CS)")
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Queue Length")
    st.pyplot(fig)

st.markdown("---")
st.subheader("🔎 Thesis Context")
st.write("""
- **DES** models individual students arriving and waiting in the Registrar’s Office.  
- **CS** models student flow as a continuous rate, showing queue length over time.  
- This prototype demonstrates how simulation can optimize **student service flow at CSPC**.  
""")
