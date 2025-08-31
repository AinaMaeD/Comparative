# 3d.py
import simpy
import random
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import math

# ============================
# DISCRETE EVENT SIMULATION
# ============================
def run_des(num_students, arrival_rate, service_time, servers):
    env = simpy.Environment()
    counter = simpy.Resource(env, capacity=servers)
    students = []

    def student(env, sid, counter, service_time):
        arrival = env.now
        service_dur = random.expovariate(1.0 / service_time)
        with counter.request() as req:
            yield req
            start = env.now
            yield env.timeout(service_dur)
            end = env.now
        students.append({
            "id": sid,
            "arrival": arrival,
            "start": start,
            "end": end,
            "wait": start - arrival,
            "service": service_dur,
            "system": end - arrival
        })

    def arrival_process(env, counter):
        for i in range(num_students):
            yield env.timeout(random.expovariate(1.0 / arrival_rate))
            env.process(student(env, i, counter, service_time))

    env.process(arrival_process(env, counter))
    env.run()
    return sorted(students, key=lambda x: x["id"])

# ============================
# CONTINUOUS SIMULATION (M/M/c)
# ============================
def run_cs(arrival_rate, service_rate, servers):
    rho = arrival_rate / (servers * service_rate)
    if rho >= 1:
        return None

    # Erlang-C
    sum_terms = sum((arrival_rate / service_rate) ** n / math.factorial(n) for n in range(servers))
    last_term = ((arrival_rate / service_rate) ** servers / math.factorial(servers)) * (1 / (1 - rho))
    p0 = 1 / (sum_terms + last_term)

    pw = last_term * p0
    Lq = (pw * rho) / (1 - rho)
    Wq = Lq / arrival_rate
    W = Wq + 1 / service_rate
    L = arrival_rate * W

    return {
        "rho": rho,
        "Pw": pw,
        "Wq": Wq,
        "W": W,
        "Lq": Lq,
        "L": L,
        "Throughput": arrival_rate
    }

# ============================
# 3D VISUALIZATION (DES)
# ============================
def build_3d(students, servers):
    counter_xs = [i * 3 for i in range(servers)]
    waiting_x = -5
    done_x = max(counter_xs) + 5

    xs, ys, zs, colors, texts = [], [], [], [], []
    for i, s in enumerate(students):
        if s["wait"] > 0:
            xs.append(waiting_x); ys.append(-i*0.2); zs.append(0)
            colors.append("blue")
            texts.append(f"Student {s['id']}<br>Waiting {s['wait']:.2f}m")
        xs.append(counter_xs[i % servers]); ys.append(0); zs.append(0)
        colors.append("red")
        texts.append(f"Student {s['id']}<br>Served {s['service']:.2f}m")
        xs.append(done_x); ys.append(i*0.1); zs.append(0)
        colors.append("green")
        texts.append(f"Student {s['id']}<br>Done at {s['end']:.2f}m")

    fig = go.Figure(data=[go.Scatter3d(
        x=xs, y=ys, z=zs,
        mode="markers",
        marker=dict(size=5, color=colors),
        text=texts, hoverinfo="text"
    )])
    fig.update_layout(scene=dict(
        xaxis_title="Flow (X)", yaxis_title="Students (Y)", zaxis_title="Z"
    ))
    return fig

# ============================
# STREAMLIT APP
# ============================
st.set_page_config(layout="wide", page_title="CSPC Registrar")
st.title("🏫 CSPC Registrar’s Office – 3D Simulation")

st.sidebar.header("⚙️ Parameters")
num_students = st.sidebar.slider("Number of Students", 50, 500, 200, 50)
arrival_rate = st.sidebar.slider("Arrival Interval (minutes)", 1, 10, 4)
service_time = st.sidebar.slider("Service Time (minutes)", 1, 10, 5)
servers = st.sidebar.slider("Service Counters", 1, 5, 2)

if st.button("▶ Run Simulation"):
    # Run DES
    students = run_des(num_students, arrival_rate, service_time, servers)
    wait_times = [s["wait"] for s in students]
    avg_wait = np.mean(wait_times)
    max_wait = np.max(wait_times)
    sim_end = max(s["end"] for s in students)
    total_service = sum(s["service"] for s in students)
    des_utilization = total_service / (servers * sim_end)
    throughput = num_students / (sim_end + 1)

    # Run CS
    service_rate = 1 / service_time
    cs_result = run_cs(1/arrival_rate, service_rate, servers)

    # Layout
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📌 Discrete-Event Simulation (DES)")
        st.write(f"**Avg Wait Time:** {avg_wait:.2f} mins")
        st.write(f"**Max Wait Time:** {max_wait:.2f} mins")
        st.write(f"**Utilization:** {des_utilization*100:.1f}%")
        st.write(f"**Throughput:** {throughput:.2f} students/min")
        fig, ax = plt.subplots()
        ax.hist(wait_times, bins=20, color="skyblue", edgecolor="black")
        ax.set_title("DES Wait Times")
        ax.set_xlabel("Minutes"); ax.set_ylabel("Students")
        st.pyplot(fig)

    with col2:
        st.subheader("📌 Continuous Simulation (CS)")
        if cs_result:
            cs_max_wait = cs_result['Wq'] * 3   # Approximate Max Wait
            st.write(f"**Expected Avg Wait (Wq):** {cs_result['Wq']:.2f} mins")
            st.write(f"**Approx. Max Wait:** {cs_max_wait:.2f} mins")
            st.write(f"**Utilization (ρ):** {cs_result['rho']*100:.1f}%")
            st.write(f"**Throughput:** {cs_result['Throughput']:.2f} students/min")

    # Comparative Table
    st.subheader("📊 Comparative Analysis")
    if cs_result:
        cs_max_wait = cs_result['Wq'] * 3
        data = {
            "Metric": ["Avg Wait", "Max Wait", "Utilization", "Throughput"],
            "DES": [
                f"{avg_wait:.2f} min",
                f"{max_wait:.2f} min",
                f"{des_utilization*100:.1f}%",
                f"{throughput:.2f} stud/min"
            ],
            "CS": [
                f"{cs_result['Wq']:.2f} min",
                f"{cs_max_wait:.2f} min",
                f"{cs_result['rho']*100:.1f}%",
                f"{cs_result['Throughput']:.2f} stud/min"
            ]
        }
    else:
        data = {
            "Metric": ["Avg Wait", "Max Wait", "Utilization", "Throughput"],
            "DES": [
                f"{avg_wait:.2f} min",
                f"{max_wait:.2f} min",
                f"{des_utilization*100:.1f}%",
                f"{throughput:.2f} stud/min"
            ],
            "CS": ["System Unstable"]*4
        }

    st.table(pd.DataFrame(data))

    # 3D Viz
    st.subheader("🌀 3D Visualization (DES)")
    st.plotly_chart(build_3d(students, servers), use_container_width=True)
