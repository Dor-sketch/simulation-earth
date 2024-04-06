"""
This module contains the GUI class for the simulation.
"""
import datetime
import tkinter as tk
from tkinter import ttk
from rules import TransitionRules
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

plt.style.use('dark_background')
class SimulationGUI:
    def __init__(self, world):
        self.world = world
        self.root = tk.Tk()
        self.root.title("My Game of Earth Simulation")

        # Create the frame for the controls
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(
            side=tk.TOP, fill=tk.X, anchor="center")

        # Create the frame for the canvas
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True,
                               anchor="center", padx=5, pady=5, ipadx=5, ipady=5)

        # Create the canvas for the world
        self.canvas = tk.Canvas(
            self.canvas_frame, width=1000, height=1000, bg='white')
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # Create the frame for the rules
        self.rules_frame = ttk.Frame(self.root)
        self.rules_frame.pack(side=tk.BOTTOM, fill=tk.X,
                              anchor="center", padx=5, pady=5, ipadx=5, ipady=5)

        self.days = 0
        self.years = 0
        self.days_per_year = 365
        self.is_simulation_running = False
        self.setup_rules_checkboxes()
        self.setup_graph()
        self.setup_controls()

    def setup_graph(self):
        fig = plt.figure(figsize=(10, 10))
        # set graph names font and size
        plt.rcParams['font.size'] = 14
        plt.rcParams['font.family'] = 'Arial'
        # Create multiple Axes objects which fills it

        self.ax1 = fig.add_subplot(2, 2, 1)  # for temperature
        # add space between graphs
        plt.subplots_adjust(hspace=0.5)

        self.ax2 = fig.add_subplot(2, 2, 2)  # for pollution
        plt.subplots_adjust(hspace=0.5)

        self.ax3 = fig.add_subplot(2, 2, 3)  # for wind speed
        plt.subplots_adjust(hspace=0.5)

        self.ax4 = fig.add_subplot(2, 2, 4)  # for rainfall

        # Create a new FigureCanvasTkAgg object which will be used to display the figure
        self.graph_canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.graph_canvas.draw()

        # Place the graph next to the canvas
        self.graph_canvas.get_tk_widget().grid(row=0, column=1)

    def update_graph(self, data1, data2, data3, data4):
        # Clear the old plots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()

        # Plot the new data
        self.ax1.plot(data1, color='red')
        self.ax2.plot(data2, color='purple')
        self.ax3.plot(data3, color='green')
        self.ax4.plot(data4, color='blue')

        # Set titles for the graphs
        self.ax1.set_title('Temperature ({})'.format(
            self.get_status_text()), fontsize=14)
        self.ax2.set_title('Pollution ({})'.format(
            self.get_status_text()), fontsize=14)
        self.ax3.set_title('Wind Speed ({})'.format(
            self.get_status_text()), fontsize=14)
        self.ax4.set_title('Rainfall ({})'.format(
            self.get_status_text()), fontsize=14)

        # add text below for total information
        self.ax1.text(0.5, -0.3, '{}'.format(self.world.get_average_temperature()),
                      size=11, ha="center", transform=self.ax1.transAxes,
                      bbox=dict(facecolor='red', alpha=0.5))
        self.ax2.text(0.5, -0.3, '{}'.format(self.world.get_average_pollution()),
                      size=11, ha="center", transform=self.ax2.transAxes,
                      bbox=dict(facecolor='purple', alpha=0.5))
        self.ax3.text(0.5, -0.3, '{}'.format(self.world.get_average_wind_speed()),
                      size=12, ha="center", transform=self.ax3.transAxes,
                      bbox=dict(facecolor='green', alpha=0.5))
        self.ax4.text(0.5, -0.3, '{}'.format(self.world.get_average_rainfall()),
                      size=11, ha="center", transform=self.ax4.transAxes,
                      bbox=dict(facecolor='blue', alpha=0.5))

        # make graphs smaller to fit the text
        plt.subplots_adjust(bottom=0.2, top=0.9, left=0.1, right=0.9)

        # Redraw the canvas
        self.graph_canvas.draw()

    def setup_controls(self):
        style = ttk.Style()
        style.configure('TButton', font=('Arial', 14))
        style.configure('TLabel', font=('Arial', 14, 'bold'))

        self.start_button = ttk.Button(
            self.control_frame, text="Start Simulation", command=self.toggle_simulation)
        self.start_button.grid(row=0, column=0, sticky=tk.EW)

        next_day_button = ttk.Button(
            self.control_frame, text="Next Day", command=self.next_day)
        next_day_button.grid(row=0, column=1, sticky=tk.EW)

        export_button = ttk.Button(
            self.control_frame, text="Export State", command=self.export_state)
        export_button.grid(row=0, column=2, sticky=tk.EW)

        export_statistics_button = ttk.Button(
            self.control_frame, text="Export Statistics", command=self.export_statistics_graph_to_png)
        export_statistics_button.grid(row=0, column=3, sticky=tk.EW)

        reset_button = ttk.Button(
            self.control_frame, text="Reset", command=self.reset)
        reset_button.grid(row=0, column=4, sticky=tk.EW)
        self.start_button.focus_set()

    def reset(self):
        self.world.reset()
        self.world.draw(self.canvas)
        self.days = 0
        self.years = 0
        self.update_date()
        self.update_graph(self.world.statistics['temperature'],
                          self.world.statistics['pollution'],
                          self.world.statistics['wind_speed'],
                          self.world.statistics['rainfall'])

    def export_statistics_graph_to_png(self, file_path='statistics.png'):
        current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = current_time + '_' + file_path
        self.graph_canvas.figure.savefig(file_name)

    def setup_rules_checkboxes(self):
        # lot of rules so we'll use a scrollable frame

        style = ttk.Style()
        style.configure('TCheckbutton', font=('Arial', 14))

        rules_scrollable_frame = ttk.Frame(self.rules_frame)
        rules_scrollable_frame.pack(side=tk.TOP, fill=tk.X)

        rules_canvas = tk.Canvas(rules_scrollable_frame)
        rules_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        rules_scrollbar = ttk.Scrollbar(
            rules_scrollable_frame, orient=tk.VERTICAL, command=rules_canvas.yview)
        rules_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        rules_canvas.configure(yscrollcommand=rules_scrollbar.set)
        rules_canvas.bind('<Configure>', lambda e: rules_canvas.configure(
            scrollregion=rules_canvas.bbox("all")))

        rules_frame = ttk.Frame(rules_canvas)
        column = 0
        col0_row = 0
        col1_row = 0
        col2_row = 0
        row = 0

        for rule in TransitionRules.rules:
            # column 0 for Weather rules, column 1 for landscape rules, column 2 for manually rules
            if rule['name'][0] in ['A', 'W', 'R', 'C', 'T']:
                column = 0
                col0_row = col0_row + 1
                row = col0_row
            elif 'manually' in rule['name']:
                column = 2
                col2_row = col2_row + 1
                row = col2_row
            else:
                column = 1
                col1_row = col1_row + 1
                row = col1_row

            # Set the initial value based on rule state
            var = tk.IntVar(value=1 if rule['enabled'] else 0)
            rule_checkbox = ttk.Checkbutton(
                rules_frame, text=rule['name'], variable=var,
                command=lambda rule=rule, var=var: self.update_rule_state(rule, var))
            rule_checkbox.grid(row=row, column=column, sticky=tk.W)

        rules_frame.pack()
        rules_canvas.create_window((0, 0), window=rules_frame, anchor="nw")

    def update_rule_state(self, rule, var):
        rule['enabled'] = bool(var.get())

    def toggle_simulation(self):
        self.is_simulation_running = not self.is_simulation_running
        if self.is_simulation_running:
            self.start_button.config(text="Pause Simulation")
            self.run_simulation()
        else:
            self.start_button.config(text="Start Simulation")

    def next_day(self):
        if self.is_simulation_running or not self.is_simulation_running:
            self.world.next_day()
            self.world.draw(self.canvas)  # Draw the new state of the world
            self.update_date()
            # Update the plot
            self.update_graph(self.world.statistics['temperature'],
                              self.world.statistics['pollution'],
                              self.world.statistics['wind_speed'],
                              self.world.statistics['rainfall'])

    def run_simulation(self):
        if self.is_simulation_running:
            self.next_day()
            self.root.after(100, self.run_simulation)

    def update_date(self):
        self.days += 1
        if self.days >= self.days_per_year:
            self.years += 1
            self.days = 0

    def get_status_text(self):
        return f"Year: {self.years}, Day: {self.days}"

    def export_state(self):
        file_path = 'exported_state.csv'
        self.world.export_state_to_csv(file_path)
        print(f"State exported to {file_path}")

    def run(self):
        self.root.mainloop()
