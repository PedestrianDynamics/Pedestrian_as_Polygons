import streamlit as st
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from shapely.geometry.polygon import Polygon
import geopandas as gpd
from longsgis import voronoiDiagram4plg
import pandas as pd
import pathlib
import jupedsim as jps
import pedpy

def plot_polygon(polygon, ax, facecolor="blue", alpha=0.5):
    """plots a polygon with its interior in matplotlib"""
    poly = gpd.GeoSeries([polygon])
    poly.plot(ax=ax, edgecolor="Black", facecolor=facecolor, alpha=alpha)

def create_circle_polygon(point, radius, quadsegs=1):
    return Polygon(point.buffer(radius, quad_segs=quadsegs).exterior.coords)

def create_voronoi(radius, quadsegs):
    bounds = Polygon([(-9, -9), (9, -9), (9, 9), (-9, 9)])
    points = [Point(x, y) for x, y in [(1, 1), (-1, 1), (-1, -1), (1, -1)]]

    circles = [create_circle_polygon(point, radius, quadsegs) for point in points]

    df = pd.DataFrame()
    df['geometry'] = circles
    df['area'] = df['geometry'].apply(lambda poly: poly.area)
    df = gpd.GeoDataFrame(df)
    voronoi = voronoiDiagram4plg(df, bounds)

    fig, ax = plt.subplots()

    for circle in circles:
        plot_polygon(circle, ax, facecolor="orange")

    for poly in voronoi["geometry"]:
        plot_polygon(poly, ax)

    ax.set_aspect('equal', 'box')

    st.pyplot(fig)


def coridor_sim(agent_amount):
    area = Polygon([(0, 0), (12, 0), (12, 4), (0, 4)], holes=[[(6.5, 1.5), (7.5, 1.5), (7.5, 2.5), (6.5, 2.5)]])
    spawning_area = Polygon([(0, 0), (5, 0), (5, 4), (0, 4)])
    num_agents = agent_amount
    pos_in_spawning_area = jps.distributions.distribute_by_number(
        polygon=spawning_area,
        number_of_agents=num_agents,
        distance_to_agents=0.6,
        distance_to_polygon=0.6,
        seed=1,
    )
    exit_area = Polygon([(11, 0), (12, 0), (12, 4), (11, 4)])

    trajectory_file = "coridor.sqlite"  # output file
    simulation = jps.Simulation(
        model=jps.CollisionFreeSpeedModel(),
        geometry=area,
        trajectory_writer=jps.SqliteTrajectoryWriter(
            output_file=pathlib.Path(trajectory_file)
        ),
    )
    exit_id = simulation.add_exit_stage(exit_area.exterior.coords[:-1])
    journey = jps.JourneyDescription([exit_id])
    journey_id = simulation.add_journey(journey)

    for pos in pos_in_spawning_area:
        simulation.add_agent(
            jps.CollisionFreeSpeedModelAgentParameters(
                journey_id=journey_id, stage_id=exit_id, position=pos, radius=0.3
            )
        )

    while simulation.agent_count() > 0:
        simulation.iterate()

def calc_polygon(poly, points_per_meter=100):
    new_polygon_points = []

    for i in range(len(poly.exterior.coords) - 1):
        p1 = poly.exterior.coords[i]
        p2 = poly.exterior.coords[i + 1]
        
        edge_length = LineString([p1, p2]).length
        
        num_points = int(edge_length * points_per_meter)
        
        delta_x = (p2[0] - p1[0]) / (num_points + 1)
        delta_y = (p2[1] - p1[1]) / (num_points + 1)
        
        for j in range(0, num_points + 2):
            new_point = Point(p1[0] + j * delta_x, p1[1] + j * delta_y)
            new_polygon_points.append(new_point)

    return Polygon(new_polygon_points)

def plot_selected_frame(selected_frame, quadsegs=2, ppm=100):
    area = Polygon([(0, 0), (12, 0), (12, 4), (0, 4)], holes=[[(6.5, 1.5), (7.5, 1.5), (7.5, 2.5), (6.5, 2.5)]])
    obstacle=Polygon([(6.5, 1.5), (7.5, 1.5), (7.5, 2.5), (6.5, 2.5)])

    obstacle=calc_polygon(obstacle, ppm)
    
    traj = pedpy.load_trajectory_from_jupedsim_sqlite(
        trajectory_file=pathlib.Path("coridor.sqlite")
    )
    data_frame = traj.data[traj.data["frame"] == selected_frame]
    radius = 0.3
    data_frame['geometry'] = data_frame.apply(lambda row: create_circle_polygon(row['point'], radius, quadsegs), axis=1)
    data_frame['area'] = data_frame['geometry'].apply(lambda x: x.area)

    obstacle_data = pd.DataFrame()
    obstacle_data["geometry"] = [obstacle]
    obstacle_data['area'] = obstacle_data['geometry'].apply(lambda x: x.area)

    used_data_frame = pd.concat([obstacle_data, data_frame[["area", "geometry"]]])
    used_data_frame = gpd.GeoDataFrame(used_data_frame)
    try:
        vd = voronoiDiagram4plg(used_data_frame, area)
        
    except Exception as e:
        print(f"frame {selected_frame} did not work properly")
        raise e
    fig = plt.figure(figsize=(20, 16))
    ax = fig.add_subplot(111)
    plot_polygon(polygon=area,ax=ax, facecolor="white")
    for poly in data_frame['geometry']:
        if selected_frame == 0:
            print(poly.exterior)
        plot_polygon(poly, ax, facecolor="orange")
    for poly in vd['geometry']:
        if poly.contains(obstacle):
            plot_polygon(poly, ax, alpha=0.5, facecolor="green")
            continue
        plot_polygon(poly, ax, alpha=0.2)

    ax.scatter(data_frame['x'], data_frame['y'], c='red')
    st.pyplot(fig)


def main():
    tab1, tab2 = st.tabs(["4 circles", "simulation"])
    with tab1:
        tab1_on = st.toggle('Activate calculation')
        if tab1_on:
            st.title("Voronoi-Plotter")
            radius = st.slider("Radius", min_value=0.1, max_value=5.0, value=0.5, step=0.01)
            quadsegs = st.slider("Quadsegs", min_value=1, max_value=5, value=3, step=1)
            create_voronoi(radius, quadsegs)

    with tab2:
        tab2_sim_on = st.toggle('Activate simulation')
        tab2_plot_on = st.toggle('Activate plot')
        if tab2_sim_on:
            agent_num = st.slider("num of agents", min_value=1, max_value=20, value=10, step=1)
            coridor_sim(agent_amount=agent_num)
        if tab2_plot_on:
            trajectory_file = "coridor.sqlite"  # output file
            traj = pedpy.load_trajectory_from_jupedsim_sqlite(
                trajectory_file=pathlib.Path(trajectory_file)
            )
            selected_frame = st.slider("frame", min_value=0, max_value=traj.data["frame"].max(), value=0, step=1)
            quadsegs_sim = st.slider("Quadsegs for Simulation", min_value=1, max_value=5, value=3, step=1)
            points_per_meter = st.slider("Points on Polygon per Meter ", min_value=0, max_value=500, value=100, step=1)
            plot_selected_frame(selected_frame, quadsegs_sim, points_per_meter)

if __name__ == "__main__":
    main()
