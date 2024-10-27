import math 

# L = 2 * dist * sin(deg/2)
# deg * 1947/360  = index

#####range set#####
# def dist_range_set():
#     dist = 0.8
#     left_deg = 195
#     right_deg = 165

#     left_idx = left_deg * (1947/360)
#     right_idx = right_deg * (1947/360)
#     total_deg = math.radians(left_deg - right_deg) # 라디안으로 변환

#     L = 2 * dist * math.sin(total_deg/2) # 현의 길이

#     print(f"left_idx = {left_idx}, right_idx = {right_idx}")
#     print(f"현의 길이 = {L}")

def L_set():
    # L = 0.2
    # dist = 0.7
    
    # # parking distance
    # L = 0.06
    # dist = 0.25
    
    set_change_degree_L = 0
    set_change_degree_R = -0
    set_change_idx_L = set_change_degree_L * (1947/360)
    set_change_idx_R = set_change_degree_R * (1947/360)
    
    total_deg = math.degrees(2 * math.asin((L / (2 * dist)))) #각도로 변환
    left_deg = 180 + (total_deg / 2)
    right_deg = 180 - (total_deg / 2)
    
    left_idx = left_deg * (1947/360) + set_change_idx_L
    right_idx = right_deg * (1947/360)+ set_change_idx_R

    
    print(f"right_idx = {right_idx}, left_idx = {left_idx}")
    print(total_deg)
    
L_set()
