import simpy
import random
import statistics
import math

# -------------------------------
# 1. DISCRETE-EVENT SIMULATION
# -------------------------------
def student(env, name, counter, service_time, wait_times):
    arrival = env.now
    with counter.request() as req:
        yield req
        wait = env.now - arrival
        wait_times.append(wait)
        yield env.timeout(random.expovariate(1.0 / service_time))

def run_des(num_students=100, arrival_rate=4, service_time=5, servers=2):
    env = simpy.Environment()
    counter = simpy.Resource(env, capacity=servers)
    wait_times = []

    def arrival_process(env, counter):
        for i in range(num_students):
            yield env.timeout(random.expovariate(1.0 / arrival_rate))
            env.process(student(env, f"Student {i}", counter, service_time, wait_times))

    env.process(arrival_process(env, counter))
    env.run()

    return statistics.mean(wait_times), wait_times


# -------------------------------
# 2. CONTINUOUS (Queueing Theory M/M/c)
# -------------------------------
def mmc_queue(arrival_rate, service_rate, servers):
    rho = arrival_rate / (servers * service_rate)  # utilization
    if rho >= 1:
        return None, None, None  # unstable system

    # Erlang C formula
    sum_terms = sum((arrival_rate / service_rate) ** n / math.factorial(n) for n in range(servers))
    last_term = ((arrival_rate / service_rate) ** servers / math.factorial(servers)) * (1 / (1 - rho))
    p0 = 1 / (sum_terms + last_term)

    pw = last_term * p0  # probability a student waits
    Lq = (pw * rho) / (1 - rho)  # expected number in queue
    Wq = Lq / arrival_rate       # expected waiting time in queue
    W = Wq + 1 / service_rate    # total time in system

    return Wq, W, rho


# -------------------------------
# MAIN COMPARISON
# -------------------------------
if __name__ == "__main__":
    # Parameters
    num_students = 200
    arrival_rate = 4     # average 1 student every 4 minutes
    service_time = 5     # average service takes 5 minutes
    service_rate = 1 / service_time
    servers = 2

    # Run DES
    des_avg_wait, wait_times = run_des(num_students, arrival_rate, service_time, servers)

    # Run Continuous
    Wq, W, rho = mmc_queue(1/arrival_rate, service_rate, servers)

    print("\n=== Comparative Analysis of Student Flow ===")
    print(f"Parameters: {num_students} students, {servers} servers")
    print("\n[Discrete-Event Simulation]")
    print(f"Average Wait Time: {des_avg_wait:.2f} minutes")
    print(f"Max Wait Time: {max(wait_times):.2f} minutes")

    print("\n[Continuous Model: M/M/c Queue]")
    print(f"Expected Wait Time: {Wq:.2f} minutes")
    print(f"Expected Time in System: {W:.2f} minutes")
    print(f"Server Utilization: {rho*100:.2f}%")