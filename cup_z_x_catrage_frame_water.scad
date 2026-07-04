// =========================================================================
// [갠트리 가변 내부 형상 측정 시스템] 좌측 배수계 정렬 및 유체 순환 완결판
// 기준 원점 (0,0,0) = X축 최좌측 상태의 컵 원통 윗면 중심 및 피스톤 플랫 일치
// 구동 모터: STS3032 고토크 스마트 서보 (서보 혼 직결 구조)
// 변경 사항: 피스톤/원통 배수구, 누수 드레인, 가이드 파이프를 모두 좌측(-X)으로 이동
// =========================================================================

$fn = 30; 
TOLERANCE = 0.2;

// --- [1] 하부 기성품 및 원통 파라미터 세팅 ---
X_STRK = 200.0;       
X_BLOCK_W = 42.0; X_BLOCK_L = 59.0;
X_PITCH_X = 20.0; X_PITCH_Y = 32.0;
X_RAIL_W = 40.0;  X_RAIL_H = 30.0;

MOTOR_W = 42.0;      MOTOR_PITCH = 31.0; MOTOR_HOLE_D = 3.5;    
MOTOR_BOSS_D = 22.0; MOTOR_BOSS_H = 2.0; SCREW_D = 8.0;         

CUP_ID = 100.0;  CUP_WALL = 6.0; CUP_OD = 112.0;     
CUP_H = 180.0;   CAGE_H = 60.0;  FLOOR_H = 10.0; PISTON_H = 25.0;     

LIP_D = 30.0;    LIP_H = 5.0;    LEAK_DRAIN_D = 4.0;    
GUIDE_PIPE_D = 8.0; BUSHING_OD = 12.0; BUSHING_H = 8.0;       
DRAIN_RADIUS = 35.0; DRAIN_D = 8.0;        

Y_OFFSET = 85.0; BRKT_H = 12.0; BRKT_D = 122.0; BRKT_ID = 62.0; Z_MOUNT_PCD = 86.0;   

// --- [2] 기성 아크릴 파이프 및 상부 카트리지 파라미터 ---
ACRYL_ID = 100.0; ACRYL_T = 3.0; ACRYL_OD = ACRYL_ID + (ACRYL_T * 2); 

REVOLVER_PCD = 220.0;    
CARTRIDGE_OD = REVOLVER_PCD + ACRYL_OD + 8; 
TOP_PLATE_H = 10.0;      

HUB_D = 60.0;            
HUB_WALL = 4.0;          
LOWER_HUB_H = 40.0;      
POCKET_DEPTH = 25.0;     

// --- [3] STS3032 스마트 서보 및 전용 플랜지 혼 파라미터 ---
SERVO_3032_L = 45.5; SERVO_3032_W = 24.7; SERVO_3032_H = 37.0; 
SERVO_HORN_D = 25.0;     
SERVO_HORN_H = 6.0;      
HORN_PCD = 18.0;         

UPPER_BRKT_H = 8.0;       
X_POS_MEASURE = 120.0;   

// --- [4] 글로벌 2020 프로파일 및 와셔 파라미터 ---
PF = 20; 
WASHER_T = 1.0;     

X_L = -290;         
X_M = 60;           
X_R = 250;          
Y_F = -200;         
Y_B = 170;          

Z_BOT = -450;       
Z_RAIL = -322;      
Z_MID = -10 - PF;   
Z_TOP = 205;        

SUPPORT_PILLAR_H = Z_TOP - PF; 

// --- 애니메이션 구동 제어 ---
X_MOVE = 60 - 60 * cos($t * 360);     
Z_MOVE = -75 + 75 * cos($t * 360);    

// =========================================================================
// [실행부] 메인 시스템 대조립
// =========================================================================
main_system_assembly();

module main_system_assembly() {
    // 1. 2020 알루미늄 프로파일 골조 프레임
    aluminum_profile_frame();
    
    // 2. 고정 하부 바닥판
    upper_fixed_base_plate();
    
    // 3. 테플론 와셔 실물 배치
    translate([-REVOLVER_PCD/2, 0, 0]) teflon_washer_dummy();
    
    // 4. STS3032 스마트 서보 및 마운트 브래킷
    translate([-REVOLVER_PCD/2, 0, 0]) upper_servo_frame_assembly();
    
    // 5. 2020 프로파일 중심축 기반 카트리지 리볼버 회전체
    translate([-REVOLVER_PCD/2, 0, WASHER_T]) 
        rotate([0, 0, $t * 360]) acryl_pipe_revolver_assembly();

    // 6. 하단 X축 레일보 직결식 유체 제어 장치 및 최적화 배관
    fluidic_control_system_assembly();

    // 7. 좌측 최하단 대용량 순환 수조 모듈 배치
    translate([-260, -165, Z_BOT + PF]) water_reservoir_tank();

    // ---------------------------------------------------------------------
    // [하부 이동식 구조물 그룹]
    // ---------------------------------------------------------------------
    color([0.4, 0.4, 0.4]) translate([0, -Y_OFFSET, -252 - 10 - X_RAIL_H/2]) x_stage_rail_dummy();
    color([0.4, 0.4, 0.4]) translate([0, Y_OFFSET, -252 - 10 - X_RAIL_H/2]) x_stage_rail_dummy();

    translate([X_MOVE, 0, 0]) {
        color([0.2, 0.2, 0.2]) translate([0, -Y_OFFSET, -252 - 10]) x_slider_block_dummy();
        color([0.2, 0.2, 0.2]) translate([0, Y_OFFSET, -252 - 10]) x_slider_block_dummy();
        color([0.2, 0.6, 0.3]) translate([0, 0, -252]) h_bridge_adapter_plate();
        z_cylinder_and_cage();
        // ★ [교정] 메인 조립체 내 황동 부싱의 안착 좌표를 -DRAIN_RADIUS(좌측)로 대칭 이동
        translate([-DRAIN_RADIUS, 0, -CUP_H - CAGE_H + FLOOR_H - BUSHING_H]) bushing_dummy();
        translate([0, 0, -CUP_H - CAGE_H]) color([0.1, 0.1, 0.1]) z_motor_dummy();
        translate([0, 0, Z_MOVE]) z_moving_parts_assembly();
    }
}

// =========================================================================
// 하단 X축 레일보 고정형 브래킷 및 좌측 최적화 배관 레이아웃
// =========================================================================
module fluidic_control_system_assembly() {
    PUMP_X = -120; PUMP_Y = Y_OFFSET; PUMP_Z = Z_RAIL + PF; 
    translate([PUMP_X, PUMP_Y, PUMP_Z]) {
        color([0.2, 0.7, 0.9]) cylinder(d=45, h=30);
        color([0.15, 0.15, 0.15]) translate([-21, -21, 30]) cube([42, 42, 40]); 
        color([0.6, 0.6, 0.6]) {
            translate([-12, -22, 15]) rotate([90, 0, 0]) cylinder(d=5, h=8); 
            translate([12, -22, 15]) rotate([90, 0, 0]) cylinder(d=5, h=8);  
        }
        color([0.5, 0.5, 0.5]) translate([-25, -20, 0]) {
            difference() {
                cube([50, 40, 4]);
                translate([8, 8, -1]) cylinder(d=4.5, h=6);
                translate([42, 8, -1]) cylinder(d=4.5, h=6);
            }
        }
    }

    VALVE_X = -190; VALVE_Y = Y_OFFSET; VALVE_Z = Z_RAIL - 30; 
    translate([VALVE_X, VALVE_Y, VALVE_Z]) {
        color([0.7, 0.5, 0.2]) cube([30, 40, 30]); 
        color([0.1, 0.1, 0.1]) translate([0, 5, 30]) cube([30, 30, 25]); 
        color([0.6, 0.6, 0.6]) {
            translate([15, -8, 15]) rotate([90, 0, 0]) cylinder(d=8, h=8); 
            translate([15, 48, 15]) rotate([90, 0, 0]) cylinder(d=8, h=8); 
        }
        color([0.4, 0.4, 0.4]) translate([-5, 5, 25]) cube([40, 30, 5]);
    }

    color([0.9, 0.9, 0.9, 0.5]) { 
        tube_curve([-150, Y_OFFSET + 30, -420], [-150, Y_OFFSET + 30, -320], 6);
        tube_curve([-150, Y_OFFSET + 30, -320], [PUMP_X - 12, PUMP_Y - 22, PUMP_Z + 15], 6);

        tube_curve([PUMP_X + 12, PUMP_Y - 22, PUMP_Z + 15], [-50, 50, -100], 6);
        tube_curve([-50, 50, -100], [20, -50, 50], 6);
        tube_curve([20, -50, 50], [X_POS_MEASURE, -20, Z_TOP - 10], 6);

        // ★ [교정] 배수구 위치가 왼쪽으로 정렬되면서 튜브가 돌지 않고 밸브로 시원하게 직결됨 (간섭 제로)
        tube_curve([X_MOVE - DRAIN_RADIUS, 0, -240], [(X_MOVE - DRAIN_RADIUS + VALVE_X)/2, 40, -300], 8);
        tube_curve([(X_MOVE - DRAIN_RADIUS + VALVE_X)/2, 40, -300], [VALVE_X + 15, VALVE_Y - 8, VALVE_Z + 15], 8);

        tube_curve([VALVE_X + 15, VALVE_Y + 48, VALVE_Z + 15], [VALVE_X + 15, VALVE_Y + 48, -410], 8);
    }
}

module tube_curve(p1, p2, d) { hull() { translate(p1) sphere(d=d); translate(p2) sphere(d=d); } }

// =========================================================================
// [좌측 정렬 교정] 하부 실린더 및 무빙 파트 그룹
// =========================================================================
module h_bridge_adapter_plate() { 
    difference() { 
        hull() { translate([0, -Y_OFFSET, 0]) cylinder(d = X_BLOCK_L + 10, h = BRKT_H); translate([0, 0, 0]) cylinder(d = BRKT_D, h = BRKT_H); translate([0, Y_OFFSET, 0]) cylinder(d = X_BLOCK_L + 10, h = BRKT_H); } 
        translate([0, -Y_OFFSET, 0]) { for(x = [-X_PITCH_X/2, X_PITCH_X/2]) { for(y = [-X_PITCH_Y/2, X_PITCH_Y/2]) { translate([x, y, -1]) cylinder(d = 4.5, h = BRKT_H + 2); } } } 
        translate([0, Y_OFFSET, 0]) { for(x = [-X_PITCH_X/2, X_PITCH_X/2]) { for(y = [-X_PITCH_Y/2, X_PITCH_Y/2]) { translate([x, y, -1]) cylinder(d = 4.5, h = BRKT_H + 2); } } } 
        translate([0, 0, -1]) cylinder(d = BRKT_ID, h = BRKT_H + 2); 
        for(a = [45, 135, 225, 315]) { rotate([0, 0, a]) translate([Z_MOUNT_PCD/2, 0, -1]) cylinder(d = 4.5, h = BRKT_H + 2); } 
        // ★ [교정] 알루미늄 아답터 보강판의 배수 스루홀 위치를 좌측(-DRAIN_RADIUS)으로 변경
        translate([-DRAIN_RADIUS, 0, -1]) cylinder(d = 14, h = BRKT_H + 2); 
    } 
}

module z_cylinder_and_cage() { 
    color([0.2, 0.5, 0.8, 0.25]) { difference() { translate([0, 0, -CUP_H]) cylinder(d=CUP_OD, h=CUP_H); translate([0, 0, -CUP_H - 0.1]) cylinder(d=CUP_ID, h=CUP_H + 0.2); } } 
    color([0.85, 0.85, 0.85, 1.0]) { 
        union() { 
            difference() { 
                translate([0, 0, -CUP_H - CAGE_H]) cylinder(d=CUP_OD, h=CAGE_H); 
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H]) cylinder(d=CUP_ID, h=CAGE_H - FLOOR_H + 0.1); 
                translate([-32.5, -CUP_OD/2 - 10, -CUP_H - CAGE_H + FLOOR_H + 5]) cube([65, CUP_OD + 20, CAGE_H - FLOOR_H - 10]); 
                translate([0, 0, -CUP_H - CAGE_H - 0.1]) cylinder(d = MOTOR_BOSS_D + TOLERANCE, h = FLOOR_H + 0.2); 
                translate([0, 0, -CUP_H - CAGE_H - 1]) { for(x = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) { for(y = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) { translate([x, y, 0]) cylinder(d = MOTOR_HOLE_D, h = FLOOR_H + 3); } } } 
                translate([0, 0, -CUP_H - CAGE_H - 1]) { for(a = [45, 135, 225, 315]) { rotate([0, 0, a]) translate([Z_MOUNT_PCD/2, 0, 0]) cylinder(d = 4.5, h = FLOOR_H + 2); } } 
                
                // ★ [교정] 누수용 탈출 드레인 구멍을 좌측(-X) 방향 수조로 직하방 조준되도록 90도 대칭 반전
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H + LEAK_DRAIN_D/2]) rotate([0, -90, 0]) cylinder(d = LEAK_DRAIN_D, h = CUP_OD/2 + 10); 
                
                // ★ [교정] 실린더 베드 바닥면의 가이드봉 관통 스루홀 및 오일리스 부싱 홈을 좌측(-DRAIN_RADIUS)으로 전면 통합 이동
                translate([-DRAIN_RADIUS, 0, -CUP_H - CAGE_H - 1]) cylinder(d = GUIDE_PIPE_D + 1.0, h = FLOOR_H + 2); 
                translate([-DRAIN_RADIUS, 0, -CUP_H - CAGE_H + FLOOR_H - BUSHING_H]) cylinder(d = BUSHING_OD + TOLERANCE, h = BUSHING_H + 0.1); 
            } 
            difference() { translate([0, 0, -CUP_H - CAGE_H + FLOOR_H]) cylinder(d=LIP_D, h=LIP_H); translate([0, 0, -CUP_H - CAGE_H + FLOOR_H - 0.1]) cylinder(d = MOTOR_BOSS_D + TOLERANCE, h = LIP_H + 0.2); } 
        } 
    } 
}

module z_moving_parts_assembly() { 
    color([0.65, 0.65, 0.65, 1.0]) difference() { 
        translate([0, 0, -PISTON_H]) cylinder(d=CUP_ID-0.5, h=PISTON_H); 
        translate([0, 0, -PISTON_H - 1]) cylinder(d = SCREW_D + 0.5, h = PISTON_H + 2); 
        translate([0, 0, -8]) cylinder(d = 15.0, h = 9, $fn = 6); 
        // ★ [교정] 내부 가동 피스톤의 메인 배수 관통홀을 좌측(-DRAIN_RADIUS)으로 이동
        translate([-DRAIN_RADIUS, 0, -PISTON_H - 1]) cylinder(d=DRAIN_D + TOLERANCE, h=PISTON_H+2); 
    } 
    translate([0, 0, 0]) rotate([180, 0, 0]) color([0.8, 0.8, 0.8]) cylinder(d=8, h=250); 
    // ★ [교정] 피스톤과 일체형으로 움직이는 물 넘침 방지용 스테인리스 가이드 수직 파이프도 좌측(-DRAIN_RADIUS)으로 정밀 연동 이동 완료
    translate([-DRAIN_RADIUS, 0, 0]) rotate([180, 0, 0]) color([0.55, 0.57, 0.6, 1.0]) difference() { cylinder(d=GUIDE_PIPE_D, h=220); translate([0,0,-1]) cylinder(d=GUIDE_PIPE_D - 2.0, h=222); } 
}

// =========================================================================
// 프레임, 수조 및 기성품 고정 모듈 (기존 설계 치수 유지)
// =========================================================================
module water_reservoir_tank() { TANK_X = 180; TANK_Y = 330; TANK_H = 80; color([0.1, 0.5, 0.8, 0.4]) { difference() { cube([TANK_X, TANK_Y, TANK_H]); translate([4, 4, 4]) cube([TANK_X - 8, TANK_Y - 8, TANK_H]); } } color([0.2, 0.6, 1.0, 0.3]) translate([4, 4, 4]) cube([TANK_X - 8, TANK_Y - 8, 55]); }
module aluminum_profile_frame() { color([0.75, 0.75, 0.75]) { translate([X_L, Y_B, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); translate([X_L, Y_F, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); translate([X_M, Y_B, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); translate([X_M, Y_F, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); translate([X_R, Y_B, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); translate([X_R, Y_F, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); } color([0.65, 0.65, 0.65]) { translate([X_L + PF, Y_B, Z_BOT]) cube([X_R - X_L - PF, PF, PF]); translate([X_L + PF, Y_F, Z_BOT]) cube([X_R - X_L - PF, PF, PF]); translate([X_L, Y_F + PF, Z_BOT]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_R, Y_F + PF, Z_BOT]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_M, Y_F + PF, Z_BOT]) cube([PF, Y_B - Y_F - PF, PF]); } color([0.8, 0.8, 0.8]) { translate([X_L, -Y_OFFSET - PF/2, Z_RAIL]) cube([X_R - X_L + PF, PF, PF]); translate([X_L, Y_OFFSET - PF/2, Z_RAIL]) cube([X_R - X_L + PF, PF, PF]); translate([X_L, Y_F + PF, Z_RAIL]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_M, Y_F + PF, Z_RAIL]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_R, Y_F + PF, Z_RAIL]) cube([PF, Y_B - Y_F - PF, PF]); } color([0.7, 0.7, 0.7]) { translate([X_L + PF, Y_B, Z_MID]) cube([X_M - X_L - PF, PF, PF]); translate([X_L + PF, Y_F, Z_MID]) cube([X_M - X_L - PF, PF, PF]); translate([X_L, Y_F + PF, Z_MID]) cube([PF, Y_B - Y_F - PF, PF]); translate([-85, Y_F + PF, Z_MID]) cube([PF, Y_B - Y_F - PF, PF]); } color([0.75, 0.75, 0.75]) { translate([X_L + PF, Y_B, Z_TOP - PF]) cube([X_R - X_L - PF, PF, PF]); translate([X_L + PF, Y_F, Z_TOP - PF]) cube([X_R - X_L - PF, PF, PF]); translate([X_L, Y_F + PF, Z_TOP - PF]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_M, Y_F + PF, Z_TOP - PF]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_R, Y_F + PF, Z_TOP - PF]) cube([PF, Y_B - Y_F - PF, PF]); } color([0.65, 0.65, 0.65]) { translate([X_L + PF, -50, Z_TOP - PF]) cube([X_M - X_L - PF, PF, PF]); translate([X_L + PF, 20, Z_TOP - PF]) cube([X_M - X_L - PF, PF, PF]); } color([0.2, 0.5, 0.8]) { translate([X_POS_MEASURE - PF/2, Y_F, Z_TOP - PF]) cube([PF, Y_B - Y_F + PF, PF]); } }
module upper_fixed_base_plate() { color([0.5, 0.5, 0.5, 0.5]) { difference() { translate([X_L, Y_F, -TOP_PLATE_H]) cube([(X_M + PF) - X_L, (Y_B + PF) - Y_F, TOP_PLATE_H]); translate([X_L - 1, Y_B - 1, -TOP_PLATE_H - 1]) cube([PF + 1 + TOLERANCE, PF + 1 + TOLERANCE, TOP_PLATE_H + 2]); translate([X_L - 1, Y_F - 1, -TOP_PLATE_H - 1]) cube([PF + 1 + TOLERANCE, PF + 1 + TOLERANCE, TOP_PLATE_H + 2]); translate([X_M - TOLERANCE, Y_B - 1, -TOP_PLATE_H - 1]) cube([PF + 1 + TOLERANCE, PF + 1 + TOLERANCE, TOP_PLATE_H + 2]); translate([X_M - TOLERANCE, Y_F - 1, -TOP_PLATE_H - 1]) cube([PF + 1 + TOLERANCE, PF + 1 + TOLERANCE, TOP_PLATE_H + 2]); translate([0, -(CUP_OD + TOLERANCE)/2, -TOP_PLATE_H - 1]) cube([CARTRIDGE_OD, CUP_OD + TOLERANCE, TOP_PLATE_H + 2]); translate([0, 0, -TOP_PLATE_H - 1]) cylinder(d=CUP_OD + TOLERANCE, h=TOP_PLATE_H + 2); translate([-REVOLVER_PCD/2, 0, -TOP_PLATE_H - 1]) cylinder(d=36, h=TOP_PLATE_H + 2); } } }
module upper_servo_frame_assembly() { color([0.4, 0.4, 0.4, 0.8]) translate([0, 0, SUPPORT_PILLAR_H]) { difference() { translate([-35, -60, 0]) cube([70, 110, UPPER_BRKT_H]); translate([-SERVO_3032_L/2, -SERVO_3032_W/2, -1]) cube([SERVO_3032_L, SERVO_3032_W, UPPER_BRKT_H + 2]); for(x = [-(SERVO_3032_L+9)/2, (SERVO_3032_L+9)/2]) { for(y = [-8, 8]) { translate([x, y, -1]) cylinder(d=2.5, h=UPPER_BRKT_H + 2); } } for(x = [-20, 20]) { translate([x, -40, -1]) cylinder(d=4.5, h=UPPER_BRKT_H + 2); translate([x, 30, -1]) cylinder(d=4.5, h=UPPER_BRKT_H + 2); } } } translate([0, 0, SUPPORT_PILLAR_H - 10]) { color([0.15, 0.15, 0.15]) { translate([-SERVO_3032_L/2, -SERVO_3032_W/2, 0]) cube([SERVO_3032_L, SERVO_3032_W, SERVO_3032_H]); translate([-(SERVO_3032_L+15)/2, -SERVO_3032_W/2, 10]) cube([SERVO_3032_L+15, SERVO_3032_W, 2.5]); } color([1, 0.4, 0]) translate([-SERVO_3032_L/2, -SERVO_3032_W/2, 12.5]) cube([SERVO_3032_L, SERVO_3032_W, 10]); } translate([0, 0, 166]) color([0.85, 0.85, 0.85]) { difference() { cylinder(d=SERVO_HORN_D, h=SERVO_HORN_H); translate([0, 0, -0.1]) cylinder(d=4, h=SERVO_HORN_H + 0.2); for(a=[0:90:270]) { rotate([0, 0, a]) translate([HORN_PCD/2, 0, -1]) cylinder(d=2.0, h=8); } } } color([0.6, 0.6, 0.6]) translate([-PF/2, -PF/2, 20]) cube([PF, PF, 146]); }
module acryl_pipe_revolver_assembly() { translate([0, 0, 0]) color([0.2, 0.2, 0.2]) difference() { union() { cylinder(d=HUB_D + 15, h=LOWER_HUB_H); for(a = [0 : 60 : 359]) { rotate([0, 0, a]) { translate([HUB_D/2, -7, 0]) cube([REVOLVER_PCD/2 - HUB_D/2, 14, LOWER_HUB_H - 5]); translate([REVOLVER_PCD/2, 0, 0]) cylinder(d=ACRYL_OD + (HUB_WALL * 2), h=LOWER_HUB_H); } } } translate([0, 0, -1]) cylinder(d=SHAFT_D, h=LOWER_HUB_H + 2); translate([-(PF+TOLERANCE)/2, -(PF+TOLERANCE)/2, -TOP_PLATE_H - 1]) cube([PF + TOLERANCE, PF + TOLERANCE, LOWER_HUB_H + TOP_PLATE_H + 2]); rotate([0, 90, 0]) translate([-20, 0, 0]) cylinder(d=4.2, h=HUB_D); for(a = [0 : 60 : 359]) { rotate([0, 0, a]) translate([REVOLVER_PCD/2, 0, -1]) { translate([0, 0, LOWER_HUB_H - POCKET_DEPTH + 1]) cylinder(d=ACRYL_OD + TOLERANCE, h=POCKET_DEPTH + 0.1); cylinder(d=CUP_ID + 0.5, h=LOWER_HUB_H + 2); } } } translate([0, 0, 145]) color([0.2, 0.2, 0.2]) difference() { union() { cylinder(d=HUB_D + 10, h=20); for(a = [0 : 60 : 359]) { rotate([0, 0, a]) { translate([HUB_D/2, -5, 0]) cube([REVOLVER_PCD/2 - HUB_D/2, 10, 20]); translate([REVOLVER_PCD/2, 0, 0]) cylinder(d=ACRYL_OD + (HUB_WALL * 2), h=20); } } } translate([-(PF+TOLERANCE)/2, -(PF+TOLERANCE)/2, -1]) cube([PF + TOLERANCE, PF + TOLERANCE, 25]); rotate([0, 90, 45]) translate([-10, 0, 0]) cylinder(d=4.2, h=HUB_D); translate([0, 0, 20 - 4]) cylinder(d=SERVO_HORN_D + 0.3, h=4.2); for(a=[0:90:270]) { rotate([0, 0, a]) translate([HORN_PCD/2, 0, -1]) cylinder(d=2.5, h=22); } for(a = [0 : 60 : 359]) { rotate([0, 0, a]) translate([REVOLVER_PCD/2, 0, -1]) cylinder(d=ACRYL_OD + TOLERANCE, h=22); } } for(a = [0 : 60 : 359]) { rotate([0, 0, a]) translate([REVOLVER_PCD/2, 0, LOWER_HUB_H - POCKET_DEPTH]) { color([0.1, 0.7, 0.9, 0.25]) difference() { cylinder(d=ACRYL_OD, h=150); translate([0, 0, -1]) cylinder(d=ACRYL_ID, h=152); } } } ring_ids = [20, 32, 44, 56, 68, 80]; ring_colors = [[1,0,0], [1,0.6,0], [1,1,0], [0,1,0], [0,0,1], [0.5,0,0.8]]; for(i = [0 : 5]) { rotate([0, 0, i * 60]) translate([REVOLVER_PCD/2, 0, 0]) { for(z_idx = [0 : 14]) { translate([0, 0, z_idx * 10]) color(ring_colors[i], 0.8) { difference() { cylinder(d=ACRYL_ID - 0.2, h=10); translate([0, 0, -0.1]) cylinder(d=ring_ids[i], h=10.2); } } } } } }
module bushing_dummy() { color([0.8, 0.55, 0.3, 1.0]) difference() { cylinder(d = BUSHING_OD, h = BUSHING_H); translate([0, 0, -1]) cylinder(d = GUIDE_PIPE_D, h = BUSHING_H + 2); } }
module z_motor_dummy() { difference() { union() { translate([-MOTOR_W/2, -MOTOR_W/2, -40]) cube([MOTOR_W, MOTOR_W, 40]); cylinder(d=MOTOR_BOSS_D, h=MOTOR_BOSS_H); } translate([0, 0, -45]) cylinder(d = SCREW_D + 2, h = 50); } }
module x_stage_rail_dummy() { translate([-50, -X_RAIL_W/2, -X_RAIL_H/2]) cube([350, X_RAIL_W, X_RAIL_H]); translate([-50, 0, 0]) rotate([0, 90, 0]) color([0.7, 0.7, 0.7]) cylinder(d=16, h=350); }
module x_slider_block_dummy() { translate([-X_BLOCK_L/2, -X_BLOCK_W/2, 0]) cube([X_BLOCK_L, X_BLOCK_W, 10]); }