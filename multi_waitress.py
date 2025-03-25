from waitress import serve
import multiprocessing
import os

def run_server(port):
    # Import the app inside each worker process
    from app import app
    print(f"Starting server on port {port} (PID: {os.getpid()})")
    serve(app, host='0.0.0.0', port=port, threads=2)

def start_servers(base_port=8000, num_workers=8):
    processes = []
    
    for i in range(num_workers):
        port = base_port + i
        p = multiprocessing.Process(target=run_server, args=(port,))
        p.start()
        processes.append(p)
        print(f"Started process on port {port}")
    
    return processes

def monitor_processes(processes):
    """Wait for all processes to complete"""
    for p in processes:
        p.join()

if __name__ == '__main__':
    # Configuration parameters
    num_workers = 4  # 8 processes for 8 performance cores
    base_port = 8000
    
    # Start servers and wait for them to complete
    processes = start_servers(base_port, num_workers)
    monitor_processes(processes)