// =========================================================================
// [갠트리 가변 내부 형상 측정 시스템] 전체 파트 최종 통합본
// 기준 원점 (0,0,0) = X축 최좌측 상태의 컵 원통 윗면 중심 및 피스톤 플랫 일치
// 구동 모터: STS3032 고토크 스마트 서보 (인코더 기반 센서리스 절대위치 제어)
// 카트리지 구조: 3t 기성 아크릴 파이프 + 하중 지지용 단차 턱 분할 허브 구조
// =========================================================================

$fn = 60; 
TOLERANCE = 0.2;

// --- [1] 하부 기성품 및 원통 파라미터 세팅 ---
// X축 스테이지 규격 (SBD-LSM-1610 쌍레일 배치)
X_STRK = 200.0;       
X_BLOCK_W = 42.0;
X_BLOCK_L = 59.0;
X_PITCH_X = 20.0; 
X_PITCH_Y = 32.0;
X_RAIL_W = 40.0;
X_RAIL_H = 30.0;

// Z축 관통형 모터 스펙 (NK4240 규격)
MOTOR_W = 42.0;
MOTOR_PITCH = 31.0;
MOTOR_HOLE_D = 3.5;    
MOTOR_BOSS_D = 22.0;   
MOTOR_BOSS_H = 2.0;    
SCREW_D = 8.0;         
LEAD_SCREW_L = 250.0;  

// Z축 원통 우물 및 피스톤 규격 (Straight 112mm 외경)
CUP_ID = 100.0;
CUP_WALL = 6.0;
CUP_OD = 112.0;     
CUP_H = 180.0;       
CAGE_H = 60.0;       
FLOOR_H = 10.0;      
PISTON_H = 25.0;     

// 방수 및 가이드 부싱 규격
LIP_D = 30.0;          
LIP_H = 5.0;           
LEAK_DRAIN_D = 4.0;    
GUIDE_PIPE_D = 10.0;   
BUSHING_OD = 12.0;     
BUSHING_H = 8.0;       
DRAIN_RADIUS = 35.0;   
DRAIN_D = 10.0;        

// H-브릿지 및 기성 레일 Y오프셋 축 정렬
Y_OFFSET = 85.0;            
BRKT_H = 12.0;        
BRKT_D = 122.0;       
BRKT_ID = 62.0;       
Z_MOUNT_PCD = 86.0;   

// --- [2] 기성 아크릴 파이프 및 상부 카트리지 파라미터 ---
ACRYL_ID = 100.0;        // 아크릴 파이프 내경
ACRYL_T  = 3.0;          // 3t 아크릴 두께 반영
ACRYL_OD = ACRYL_ID + (ACRYL_T * 2); // 외경 106mm

REVOLVER_PCD = 220.0;    // 파이프 간 외경 기준 4mm 안전 격벽 마진 확보
CARTRIDGE_OD = REVOLVER_PCD + ACRYL_OD + 8; // 정사각형 바닥판 한 변 길이 (약 334mm)
TOP_PLATE_H = 10.0;      // 고정 바닥판 두께

HUB_D = 60.0;            // 중앙 회전 허브 코어 직경
SHAFT_D = 12.0;          // 중심 구동축 샤프트 직경
HUB_WALL = 4.0;          // 파이프를 감싸는 소켓 외벽 살두께

LOWER_HUB_H = 40.0;      // 하중을 안정적으로 지탱하기 위한 하부 허브 높이
POCKET_DEPTH = 25.0;     // 아크릴 파이프가 삽입되는 깊이 (바닥 15mm가 단단한 지지 턱이 됨)

// --- [3] STS3032 고토크 스마트 서보 스펙 파라미터 ---
SERVO_3032_L = 45.5;      // 서보 바디 길이
SERVO_3032_W = 24.7;      // 서보 바디 폭
SERVO_3032_H = 37.0;      // 서보 바디 높이
SERVO_HORN_D = 25.0;     // 서보 출력축 플랜지 혼 직경

SUPPORT_PILLAR_H = 175.0; // 카트리지 파이프 수직 회피용 지지 기둥 높이
UPPER_BRKT_H = 8.0;       // 상부 모터 마운트 플레이트 두께

// --- [4] 애니메이션 구동 제어 (t=0일 때 최좌측 원점 도킹 및 피스톤 최상단 배치) ---
X_MOVE = 60 - 60 * cos($t * 360);     // X=0(좌측 끝 링 적층위치)에서 시작하여 우측 측정구역 왕복
Z_MOVE = -75 + 75 * cos($t * 360);    // 피스톤 상하 구동 (-150mm ~ 0mm 플랫 상태 구현)

// =========================================================================
// [실행부] 메인 시스템 대조립
// =========================================================================
main_system_assembly();

module main_system_assembly() {
    
    // ---------------------------------------------------------------------
    // [고정 상부 구조물 프레임 그룹] (X축 이동에 독립되어 고정됨)
    // ---------------------------------------------------------------------
    // A. 카트리지 정사각형 고정 바닥판 (Z=0 플랫 매칭)
    upper_fixed_base_plate();
    
    // B. STS3032 스마트 서보 구동 하우징부 (회전축 X = -110 고정 프레임)
    translate([-REVOLVER_PCD/2, 0, 0]) upper_servo_frame_assembly();
    
    // C. 아크릴 카트리지 리볼버 회전체 (절대 인코더 동기화 회전 비주얼라이즈)
    translate([-REVOLVER_PCD/2, 0, 0]) 
        rotate([0, 0, $t * 360]) acryl_pipe_revolver_assembly();

    // ---------------------------------------------------------------------
    // [고정 하부 프레임 그룹] (X축 레일 가이드 - 최좌측 시프트 완료)
    // ---------------------------------------------------------------------
    color([0.4, 0.4, 0.4]) translate([0, -Y_OFFSET, -252 - 10 - X_RAIL_H/2]) x_stage_rail_dummy();
    color([0.4, 0.4, 0.4]) translate([0, Y_OFFSET, -252 - 10 - X_RAIL_H/2]) x_stage_rail_dummy();

    // ---------------------------------------------------------------------
    // [X축 동기 구동 이동 그룹] (X_MOVE에 따라 원통 전체가 슬라이딩)
    // ---------------------------------------------------------------------
    translate([X_MOVE, 0, 0]) {
        
        // 무빙 슬라이더 블록
        color([0.2, 0.2, 0.2]) translate([0, -Y_OFFSET, -252 - 10]) x_slider_block_dummy();
        color([0.2, 0.2, 0.2]) translate([0, Y_OFFSET, -252 - 10]) x_slider_block_dummy();
        
        // [H-브릿지 브래킷]
        color([0.2, 0.6, 0.3]) translate([0, 0, -252]) h_bridge_adapter_plate();
        
        // [Z축 원통 및 케이지 모듈]
        z_cylinder_and_cage();
        
        // 하부 오일레스 부싱
        translate([DRAIN_RADIUS, 0, -CUP_H - CAGE_H + FLOOR_H - BUSHING_H]) bushing_dummy();
        
        // Z축 관통형 모터
        translate([0, 0, -CUP_H - CAGE_H]) color([0.1, 0.1, 0.1]) z_motor_dummy();
        
        // Z축 연동 가동 피스톤 (Z_MOVE=0 일 때 원통 상단 Z=0과 칼같이 일치)
        translate([0, 0, Z_MOVE]) z_moving_parts_assembly();
    }
}

// =========================================================================
// [상부 구조물 모듈 상세 설계]
// =========================================================================

// 1. 카트리지 정사각형 고정 바닥판
module upper_fixed_base_plate() {
    color([0.5, 0.5, 0.5, 0.5]) { 
        difference() {
            // 카트리지 하중 전체를 안정적으로 받아주는 정사각형 플레이트
            translate([-REVOLVER_PCD/2, 0, -TOP_PLATE_H/2]) 
                cube([CARTRIDGE_OD, CARTRIDGE_OD, TOP_PLATE_H], center=true);
            
            // [탈출 슬롯 가공] 원점에서부터 우측(+X) 끝까지 원통 외경 폭으로 시원하게 관통 커팅
            translate([0, -(CUP_OD + TOLERANCE)/2, -TOP_PLATE_H - 1]) 
                cube([CARTRIDGE_OD, CUP_OD + TOLERANCE, TOP_PLATE_H + 2]);
            
            // 원점(0,0) 자리에 딱 맞는 원호 가이드 형상 유지를 위한 재커팅
            translate([0, 0, -TOP_PLATE_H - 1]) 
                cylinder(d=CUP_OD + TOLERANCE, h=TOP_PLATE_H + 2);
            
            // 중심 회전축 통과 홀
            translate([-REVOLVER_PCD/2, 0, -TOP_PLATE_H - 1])
                cylinder(d=SHAFT_D + 4, h=TOP_PLATE_H + 2); 
        }
    }
}

// 2. STS3032 스마트 서보 마운트 및 상부 지지 3필러 프레임
module upper_servo_frame_assembly() {
    // 알루미늄 필러 기둥 (정사각형 바닥판 모서리 3점 배치 - 우측 탈출 슬롯 오픈 구조 조건문 제어)
    pillar_offset = CARTRIDGE_OD/2 - 15;
    color([0.6, 0.6, 0.6]) {
        for(x = [-pillar_offset, pillar_offset]) {
            for(y = [-pillar_offset, pillar_offset]) {
                if (!(x > 0 && abs(y) < CUP_OD)) {
                    translate([x, y, 0]) cylinder(d=12, h=SUPPORT_PILLAR_H);
                }
            }
        }
    }
    
    // STS3032 마운트 탑 플레이트 (Z = 175mm 위치)
    color([0.4, 0.4, 0.4, 0.7]) translate([0, 0, SUPPORT_PILLAR_H]) {
        difference() {
            cylinder(d=HUB_D + 70, h=UPPER_BRKT_H);
            
            // STS3032 바디 안착용 정밀 사각 관통 홈
            translate([-SERVO_3032_L/2, -SERVO_3032_W/2, -1])
                cube([SERVO_3032_L, SERVO_3032_W, UPPER_BRKT_H + 2]);
                
            // 서보 마운트 플랜지 볼트 홀 4개
            for(x = [-(SERVO_3032_L+10)/2, (SERVO_3032_L+10)/2]) {
                for(y = [-SERVO_3032_W/4, SERVO_3032_W/4]) {
                    translate([x, y, -1]) cylinder(d=3.0, h=UPPER_BRKT_H + 2);
                }
            }
        }
    }
    
    // STS3032 스마트 서보 기성품 실물 더미 (거꾸로 체결되어 동력 직결 하강)
    translate([0, 0, SUPPORT_PILLAR_H + 10]) {
        color([0.15, 0.15, 0.15]) { 
            translate([-SERVO_3032_L/2, -SERVO_3032_W/2, 0]) cube([SERVO_3032_L, SERVO_3032_W, SERVO_3032_H]);
            translate([-(SERVO_3032_L+15)/2, -SERVO_3032_W/2, 22]) cube([SERVO_3032_L+15, SERVO_3032_W, 3]); // 날개
        }
        color([1, 0.4, 0]) translate([-SERVO_3032_L/2, -SERVO_3032_W/2, -5]) cube([SERVO_3032_L, SERVO_3032_W, 5]); // 알루미늄 케이스 포인트
    }
    
    // 서보 출력축 혼(Horn) 플랜지 및 12mm 동력 샤프트
    color([0.8, 0.8, 0.8]) {
        translate([0, 0, SUPPORT_PILLAR_H - 5]) cylinder(d=SERVO_HORN_D, h=5);
        translate([0, 0, 30]) cylinder(d=SHAFT_D, h=SUPPORT_PILLAR_H - 35);
    }
}

// 3. 3t 아크릴 파이프 카트리지 + 단차 턱 허브 일체형 리볼버
module acryl_pipe_revolver_assembly() {
    
    // [허브 파트 1] 하부 헤비 턱 허브 (높이 40mm, 전단 응력 및 수직 하중 분산 코어)
    translate([0, 0, 0]) color([0.2, 0.2, 0.2]) difference() {
        union() {
            cylinder(d=HUB_D + 15, h=LOWER_HUB_H); 
            for(a = [0 : 60 : 359]) {
                rotate([0, 0, a]) {
                    // 구동 토크 파스를 단단히 연결해 줄 강화 보강 리브 (두께 14mm)
                    translate([HUB_D/2, -7, 0]) cube([REVOLVER_PCD/2 - HUB_D/2, 14, LOWER_HUB_H - 5]);
                    // 아크릴 파이프 하단 슬리브 홀더 외벽
                    translate([REVOLVER_PCD/2, 0, 0]) 
                        cylinder(d=ACRYL_OD + (HUB_WALL * 2), h=LOWER_HUB_H);
                }
            }
        }
        translate([0, 0, -1]) cylinder(d=SHAFT_D, h=LOWER_HUB_H + 2);
        
        // ★ [하중 분산 단차 턱 가공 코어]
        for(a = [0 : 60 : 359]) {
            rotate([0, 0, a]) translate([REVOLVER_PCD/2, 0, -1]) {
                // 1. 위에서 25mm 깊이만큼 외경 106mm 소켓 가공 (3t 아크릴 파이프가 쏙 안착될 안착 홈)
                translate([0, 0, LOWER_HUB_H - POCKET_DEPTH + 1])
                    cylinder(d=ACRYL_OD + TOLERANCE, h=POCKET_DEPTH + 0.1);
                
                // 2. 바닥 쪽 15mm 구간은 링이 통과할 수 있도록 내경 100.5mm로 완전히 통자 관통!
                // 이를 통해 아크릴 파이프 단면은 단차에 걸치고, 도넛 링들만 걸림 없이 바닥 Z=0까지 내려옵니다.
                cylinder(d=CUP_ID + 0.5, h=LOWER_HUB_H + 2);
            }
        }
    }
    
    // [허브 파트 2] 상부 정렬 지지 허브 (높이 20mm, 수직 회전 관성 정렬 브래킷)
    translate([0, 0, 145]) color([0.2, 0.2, 0.2]) difference() {
        union() {
            cylinder(d=HUB_D + 10, h=20);
            for(a = [0 : 60 : 359]) {
                rotate([0, 0, a]) {
                    translate([HUB_D/2, -5, 0]) cube([REVOLVER_PCD/2 - HUB_D/2, 10, 20]);
                    translate([REVOLVER_PCD/2, 0, 0]) 
                        cylinder(d=ACRYL_OD + (HUB_WALL * 2), h=20);
                }
            }
        }
        translate([0, 0, -1]) cylinder(d=SHAFT_D, h=25);
        for(a = [0 : 60 : 359]) {
            rotate([0, 0, a]) translate([REVOLVER_PCD/2, 0, -1])
                cylinder(d=ACRYL_OD + TOLERANCE, h=22);
        }
    }

    // [기성품 파트 3] 3t 투명 아크릴 파이프 실물 (외경 106mm, 내경 100mm, 길이 150mm)
    for(a = [0 : 60 : 359]) {
        rotate([0, 0, a]) translate([REVOLVER_PCD/2, 0, LOWER_HUB_H - POCKET_DEPTH]) {
            color([0.1, 0.7, 0.9, 0.25]) difference() {
                cylinder(d=ACRYL_OD, h=150); 
                translate([0, 0, -1]) cylinder(d=ACRYL_ID, h=152);
            }
        }
    }
    
    // ★ [위치 개정 반영] 내부 가변 도넛 링 적재 비주얼 샘플링 데이터
    // 하부 허브 내경이 100.5mm로 하단까지 열려있으므로, 링 최하단이 고정 바닥판인 Z=0에 정확히 밀착 안착됩니다.
    ring_ids = [20, 32, 44, 56, 68, 80];
    ring_colors = [[1,0,0], [1,0.6,0], [1,1,0], [0,1,0], [0,0,1], [0.5,0,0.8]];
    
    for(i = [0 : 5]) {
        rotate([0, 0, i * 60]) translate([REVOLVER_PCD/2, 0, 0]) { 
            for(z_idx = [0 : 14]) {
                translate([0, 0, z_idx * 10]) color(ring_colors[i], 0.8) {
                    difference() {
                        cylinder(d=ACRYL_ID - 0.2, h=10); // 슬라이딩 원활 공차
                        translate([0, 0, -0.1]) cylinder(d=ring_ids[i], h=10.2); 
                    }
                }
            }
        }
    }
}


// =========================================================================
// [4] 하부 이동식 구조물 및 기성 부품 더미 모듈 (기존 치수 철저 유지)
// =========================================================================

// H-브릿지 무빙 어댑터 플레이트
module h_bridge_adapter_plate() {
    difference() {
        hull() {
            translate([0, -Y_OFFSET, 0]) cylinder(d = X_BLOCK_L + 10, h = BRKT_H);
            translate([0, 0, 0]) cylinder(d = BRKT_D, h = BRKT_H);
            translate([0, Y_OFFSET, 0]) cylinder(d = X_BLOCK_L + 10, h = BRKT_H);
        }
        translate([0, -Y_OFFSET, 0]) {
            for(x = [-X_PITCH_X/2, X_PITCH_X/2]) {
                for(y = [-X_PITCH_Y/2, X_PITCH_Y/2]) {
                    translate([x, y, -1]) cylinder(d = 4.5, h = BRKT_H + 2);
                }
            }
        }
        translate([0, Y_OFFSET, 0]) {
            for(x = [-X_PITCH_X/2, X_PITCH_X/2]) {
                for(y = [-X_PITCH_Y/2, X_PITCH_Y/2]) {
                    translate([x, y, -1]) cylinder(d = 4.5, h = BRKT_H + 2);
                }
            }
        }
        translate([0, 0, -1]) cylinder(d = BRKT_ID, h = BRKT_H + 2);
        for(a = [45, 135, 225, 315]) {
            rotate([0, 0, a]) translate([Z_MOUNT_PCD/2, 0, -1]) cylinder(d = 4.5, h = BRKT_H + 2);
        }
        translate([DRAIN_RADIUS, 0, -1]) cylinder(d = 14, h = BRKT_H + 2);
    }
}

// Z축 테스트베드 원통 우물 실린더 및 챔버 바디
module z_cylinder_and_cage() {
    color([0.2, 0.5, 0.8, 0.25]) {
        difference() {
            translate([0, 0, -CUP_H]) cylinder(d=CUP_OD, h=CUP_H);
            translate([0, 0, -CUP_H - 0.1]) cylinder(d=CUP_ID, h=CUP_H + 0.2);
        }
    }
    color([0.85, 0.85, 0.85, 1.0]) {
        union() {
            difference() {
                translate([0, 0, -CUP_H - CAGE_H]) cylinder(d=CUP_OD, h=CAGE_H);
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H]) cylinder(d=CUP_ID, h=CAGE_H - FLOOR_H + 0.1); 
                translate([-32.5, -CUP_OD/2 - 10, -CUP_H - CAGE_H + FLOOR_H + 5]) cube([65, CUP_OD + 20, CAGE_H - FLOOR_H - 10]);
                translate([0, 0, -CUP_H - CAGE_H - 0.1]) cylinder(d = MOTOR_BOSS_D + TOLERANCE, h = FLOOR_H + 0.2);
                translate([0, 0, -CUP_H - CAGE_H - 1]) {
                    for(x = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) {
                        for(y = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) {
                            translate([x, y, 0]) cylinder(d = MOTOR_HOLE_D, h = FLOOR_H + 3);
                        }
                    }
                }
                translate([0, 0, -CUP_H - CAGE_H - 1]) {
                    for(a = [45, 135, 225, 315]) {
                        rotate([0, 0, a]) translate([Z_MOUNT_PCD/2, 0, 0]) cylinder(d = 4.5, h = FLOOR_H + 2);
                    }
                }
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H + LEAK_DRAIN_D/2]) rotate([0, 90, 0]) cylinder(d = LEAK_DRAIN_D, h = CUP_OD + 10, center=true);
                translate([DRAIN_RADIUS, 0, -CUP_H - CAGE_H - 1]) cylinder(d = GUIDE_PIPE_D + 1.0, h = FLOOR_H + 2); 
                translate([DRAIN_RADIUS, 0, -CUP_H - CAGE_H + FLOOR_H - BUSHING_H]) cylinder(d = BUSHING_OD + TOLERANCE, h = BUSHING_H + 0.1);
            }
            difference() {
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H]) cylinder(d=LIP_D, h=LIP_H);
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H - 0.1]) cylinder(d = MOTOR_BOSS_D + TOLERANCE, h = LIP_H + 0.2);
            }
        }
    }
}

// Z축 상하이동 피스톤 및 내부 가이드 로드 배수 유닛
module z_moving_parts_assembly() {
    color([0.65, 0.65, 0.65, 1.0]) difference() {
        translate([0, 0, -PISTON_H]) cylinder(d=CUP_ID-0.5, h=PISTON_H);
        translate([0, 0, -PISTON_H - 1]) cylinder(d = SCREW_D + 0.5, h = PISTON_H + 2); 
        translate([0, 0, -8]) cylinder(d = 15.0, h = 9, $fn = 6); 
        translate([DRAIN_RADIUS, 0, -PISTON_H - 1]) cylinder(d=DRAIN_D + TOLERANCE, h=PISTON_H+2); 
    }
    translate([0, 0, 0]) rotate([180, 0, 0]) color([0.8, 0.8, 0.8]) cylinder(d=8, h=250);
    translate([35, 0, 0]) rotate([180, 0, 0]) color([0.55, 0.57, 0.6, 1.0]) difference() {
        cylinder(d=GUIDE_PIPE_D, h=220);
        translate([0,0,-1]) cylinder(d=GUIDE_PIPE_D - 1.6, h=222);
    }
}

// 기성 하드웨어 더미 요소들
module bushing_dummy() { color([0.8, 0.55, 0.3, 1.0]) difference() { cylinder(d = BUSHING_OD, h = BUSHING_H); translate([0, 0, -1]) cylinder(d = GUIDE_PIPE_D, h = BUSHING_H + 2); } }
module z_motor_dummy() { difference() { union() { translate([-MOTOR_W/2, -MOTOR_W/2, -40]) cube([MOTOR_W, MOTOR_W, 40]); cylinder(d=MOTOR_BOSS_D, h=MOTOR_BOSS_H); } translate([0, 0, -45]) cylinder(d = SCREW_D + 2, h = 50); } }
module x_stage_rail_dummy() { translate([-50, -X_RAIL_W/2, -X_RAIL_H/2]) cube([350, X_RAIL_W, X_RAIL_H]); translate([-50, 0, 0]) rotate([0, 90, 0]) color([0.7, 0.7, 0.7]) cylinder(d=16, h=350); }
module x_slider_block_dummy() { translate([-X_BLOCK_L/2, -X_BLOCK_W/2, 0]) cube([X_BLOCK_L, X_BLOCK_W, 10]); }