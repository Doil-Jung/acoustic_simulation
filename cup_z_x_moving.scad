// =========================================================================
// [갠트리 초경량 실전판] 가변 내부 형상 측정 시스템 (하부 플랜지 제거 및 직결 구조)
// 상부 마이크 공간 100% 개방 / 원통 하단 직결 볼트홀 / 브래킷 내경 최적화 완료
// =========================================================================

$fn = 60; 
TOLERANCE = 0.2;

// --- [1] 기성품 및 도면 파라미터 세팅 ---

// 1. X축 스테이지 규격 (SBD-LSM-1610 쌍레일 배치)
X_STRK = 200.0;       
X_BLOCK_W = 42.0;
X_BLOCK_L = 59.0;
X_PITCH_X = 20.0; 
X_PITCH_Y = 32.0;
X_RAIL_W = 40.0;
X_RAIL_H = 30.0;

// 2. Z축 관통형 모터 스펙 (NK4240 규격)
MOTOR_W = 42.0;
MOTOR_PITCH = 31.0;
MOTOR_HOLE_D = 3.5;    
MOTOR_BOSS_D = 22.0;   
MOTOR_BOSS_H = 2.0;    
SCREW_D = 8.0;         
LEAD_SCREW_L = 250.0;  

// 3. Z축 원통 우물 및 피스톤 규격 (플랜지 제거, Straight 112mm 외경)
CUP_ID = 100.0;
CUP_WALL = 6.0;
CUP_OD = 112.0;     // 원통 최하단까지 112mm 단일 외경 유지
CUP_H = 180.0;       
CAGE_H = 60.0;       
FLOOR_H = 10.0;      
PISTON_H = 25.0;      

// 4. 방수 및 가이드 부싱 규격
LIP_D = 30.0;          
LIP_H = 5.0;           
LEAK_DRAIN_D = 4.0;    
GUIDE_PIPE_D = 10.0;   
BUSHING_OD = 12.0;     
BUSHING_H = 8.0;       
DRAIN_RADIUS = 35.0;   
DRAIN_D = 10.0;        

// 5. H-브릿지 개정 파라미터 (★내경 축소 및 직결 홀 배치)
Y_OFFSET = 85.0;            
RAIL2_Y = Y_OFFSET * 2;     
BRKT_H = 12.0;        
BRKT_D = 122.0;       // 플랜지가 사라져서 브래킷 외경도 122mm로 슬림화
BRKT_ID = 62.0;       // ★ 내경을 62mm로 축소 (NEMA17 모터가 쏙 통과하는 크기)
Z_MOUNT_PCD = 86.0;   // ★ 원통 바닥면과 브래킷을 직결하는 볼트 PCD (반경 43mm)

// 애니메이션 구동 범위
X_MOVE = 80 * sin($t * 360);       
Z_MOVE = -75 + 75 * cos($t * 360); 

// =========================================================================
// [실행부] 갠트리 레이아웃 시스템 대조립
// =========================================================================
main_system_assembly();

module main_system_assembly() {
    // 1. [고정 바닥] X축 1번 레일
    color([0.4, 0.4, 0.4]) translate([0, 0, -252 - 10 - X_RAIL_H/2]) x_stage_rail_dummy();
    
    // 2. [고정 바닥] X축 2번 레일 (Y = 170mm)
    color([0.4, 0.4, 0.4]) translate([0, RAIL2_Y, -252 - 10 - X_RAIL_H/2]) x_stage_rail_dummy();

    // 3. [X축 동기 구동 그룹]
    translate([X_MOVE, 0, 0]) {
        
        // 3-1. X축 1번 무빙 슬라이더 블록 (Y = 0)
        color([0.2, 0.2, 0.2]) translate([0, 0, -252 - 10]) x_slider_block_dummy();
        
        // 3-2. X축 2번 무빙 슬라이더 블록 (Y = 170mm)
        color([0.2, 0.2, 0.2]) translate([0, RAIL2_Y, -252 - 10]) x_slider_block_dummy();
        
        // 3-3. [H-브릿지 브래킷] (내경이 축소되어 원통 바닥을 받쳐주는 형태로 진화)
        color([0.2, 0.6, 0.3]) translate([0, 0, -252]) h_bridge_adapter_plate();
        
        // 3-4. [Z축 모듈] (브래킷 윗면인 Z = -240 지점에 정확히 복안착)
        translate([0, Y_OFFSET, 0]) {
            z_cylinder_and_cage();
            
            // 바닥판 포켓 홈에 안착되는 고정 오일리스 부싱
            translate([DRAIN_RADIUS, 0, -CUP_H - CAGE_H + FLOOR_H - BUSHING_H]) bushing_dummy();
            
            // Z축 관통형 모터 (브래킷의 축소된 내경 홈 안으로 들어가 원통 바닥에 밀착됨)
            translate([0, 0, -CUP_H - CAGE_H]) color([0.1, 0.1, 0.1]) z_motor_dummy();
            
            // Z축 연동 가동 그룹
            translate([0, 0, Z_MOVE]) z_moving_parts_assembly();
        }
    }
}

// =========================================================================
// [어댑터 브래킷] 내경이 축소된 슬림형 H-브릿지 플레이트
// =========================================================================
module h_bridge_adapter_plate() {
    difference() {
        hull() {
            translate([0, 0, 0]) cylinder(d = X_BLOCK_L + 10, h = BRKT_H);
            translate([0, Y_OFFSET, 0]) cylinder(d = BRKT_D, h = BRKT_H);
            translate([0, RAIL2_Y, 0]) cylinder(d = X_BLOCK_L + 10, h = BRKT_H);
        }
        
        // 1번 X블록 체결용 M4 홀 (20x32)
        for(x = [-X_PITCH_X/2, X_PITCH_X/2]) {
            for(y = [-X_PITCH_Y/2, X_PITCH_Y/2]) {
                translate([x, y, -1]) cylinder(d = 4.5, h = BRKT_H + 2);
            }
        }
        
        // 2번 X블록 체결용 M4 홀 (Y=170 기준 20x32)
        translate([0, RAIL2_Y, 0]) {
            for(x = [-X_PITCH_X/2, X_PITCH_X/2]) {
                for(y = [-X_PITCH_Y/2, X_PITCH_Y/2]) {
                    translate([x, y, -1]) cylinder(d = 4.5, h = BRKT_H + 2);
                }
            }
        }
        
        // ★ [설계 변경] 내경 축소: 모터만 통과하고 원통 바닥면은 붙잡아주는 지지 대형 홀
        translate([0, Y_OFFSET, -1]) cylinder(d = BRKT_ID, h = BRKT_H + 2);
        
        // ★ [설계 변경] 원통 바닥면과 직접 결합하는 직결 M4 볼트 홀 4개 (PCD 86)
        translate([0, Y_OFFSET, 0]) {
            for(a = [45, 135, 225, 315]) {
                rotate([0, 0, a]) translate([Z_MOUNT_PCD/2, 0, -1]) cylinder(d = 4.5, h = BRKT_H + 2);
            }
        }
        
        // 가이드 배수 파이프 통과 여유 홀
        translate([0, Y_OFFSET, 0]) {
            translate([DRAIN_RADIUS, 0, -1]) cylinder(d = 14, h = BRKT_H + 2);
        }
    }
}

// =========================================================================
// [Z축 원통 모듈] 하부 플랜지 영구 삭제 및 바닥 직결 볼트홀 반영 버전
// =========================================================================
module z_cylinder_and_cage() {
    
    // 상부 원통 우물 바디 (투명 블루)
    color([0.2, 0.5, 0.8, 0.25]) {
        difference() {
            translate([0, 0, -CUP_H]) cylinder(d=CUP_OD, h=CUP_H);
            translate([0, 0, -CUP_H - 0.1]) cylinder(d=CUP_ID, h=CUP_H + 0.2);
        }
    }
    
    // 하부 조립 케이지 (불투명 그레이 / 외곽 거추장스러운 플랜지 날개 완전 제거)
    color([0.85, 0.85, 0.85, 1.0]) {
        union() {
            difference() {
                // 원통 외경 112mm가 하단 끝까지 뚝 떨어지는 깔끔한 형상
                translate([0, 0, -CUP_H - CAGE_H]) cylinder(d=CUP_OD, h=CAGE_H);
                
                // 내경 100mm 내부 챔버 가공
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H]) cylinder(d=CUP_ID, h=CAGE_H - FLOOR_H + 0.1); 
                
                // 정면 작업창
                translate([-32.5, -CUP_OD/2 - 10, -CUP_H - CAGE_H + FLOOR_H + 5]) 
                    cube([65, CUP_OD + 20, CAGE_H - FLOOR_H - 10]);
                
                // 모터 보스 안착 시트
                translate([0, 0, -CUP_H - CAGE_H - 0.1]) 
                    cylinder(d = MOTOR_BOSS_D + TOLERANCE, h = FLOOR_H + 0.2);
                    
                // 42각 모터 고정용 M3 관통 홀 4개
                translate([0, 0, -CUP_H - CAGE_H - 1]) {
                    for(x = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) {
                        for(y = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) {
                            translate([x, y, 0]) cylinder(d = MOTOR_HOLE_D, h = FLOOR_H + 3);
                        }
                    }
                }
                
                // ★ [설계 변경] 원통 최하단 바닥면에 추가된 브래킷 직결용 M4 볼트 홀 4개 (PCD 86)
                // 여기에 인서트 너트를 심거나 태핑하여 초록색 브래킷과 아래서 위로 바로 체결합니다.
                translate([0, 0, -CUP_H - CAGE_H - 1]) {
                    for(a = [45, 135, 225, 315]) {
                        rotate([0, 0, a]) translate([Z_MOUNT_PCD/2, 0, 0]) cylinder(d = 4.5, h = FLOOR_H + 2);
                    }
                }
                
                // 누수 배출구 홀
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H + LEAK_DRAIN_D/2]) 
                    rotate([0, 90, 0]) cylinder(d = LEAK_DRAIN_D, h = CUP_OD + 10, center=true);

                // 가이드 파이프 통과 홀
                translate([DRAIN_RADIUS, 0, -CUP_H - CAGE_H - 1]) cylinder(d = GUIDE_PIPE_D + 1.0, h = FLOOR_H + 2); 
                    
                // 오일리스 부싱 포켓 홈
                translate([DRAIN_RADIUS, 0, -CUP_H - CAGE_H + FLOOR_H - BUSHING_H]) 
                    cylinder(d = BUSHING_OD + TOLERANCE, h = BUSHING_H + 0.1);
            }
            
            // 중앙 내부 방수 턱 (독립 안착 버그 픽스 유지)
            difference() {
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H]) cylinder(d=LIP_D, h=LIP_H);
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H - 0.1]) 
                    cylinder(d = MOTOR_BOSS_D + TOLERANCE, h = LIP_H + 0.2);
            }
        }
    }
}

// =========================================================================
// 기타 하드웨어 모듈 스펙 (시각화 고정 데이터)
// =========================================================================
module z_moving_parts_assembly() {
    color([0.65, 0.65, 0.65, 1.0]) difference() {
        cylinder(d=CUP_ID-0.5, h=PISTON_H);
        translate([0, 0, -1]) cylinder(d = SCREW_D + 0.5, h = PISTON_H + 2); 
        translate([0, 0, PISTON_H - 8]) cylinder(d = 15.0, h = 9, $fn = 6); 
        translate([DRAIN_RADIUS, 0, -1]) cylinder(d=DRAIN_D + TOLERANCE, h=PISTON_H+2); 
    }
    translate([0, 0, PISTON_H]) rotate([180, 0, 0]) color([0.8, 0.8, 0.8]) cylinder(d=8, h=250);
    translate([35, 0, PISTON_H]) rotate([180, 0, 0]) color([0.55, 0.57, 0.6, 1.0]) 
        difference() {
            cylinder(d=GUIDE_PIPE_D, h=220);
            translate([0,0,-1]) cylinder(d=GUIDE_PIPE_D - 1.6, h=222);
        }
}

module bushing_dummy() {
    color([0.8, 0.55, 0.3, 1.0]) {
        difference() {
            cylinder(d = BUSHING_OD, h = BUSHING_H);
            translate([0, 0, -1]) cylinder(d = GUIDE_PIPE_D, h = BUSHING_H + 2);
        }
    }
}

module z_motor_dummy() {
    difference() {
        union() {
            translate([-MOTOR_W/2, -MOTOR_W/2, -40]) cube([MOTOR_W, MOTOR_W, 40]); 
            cylinder(d=MOTOR_BOSS_D, h=MOTOR_BOSS_H); 
        }
        translate([0, 0, -45]) cylinder(d = SCREW_D + 2, h = 50); 
    }
}

module x_stage_rail_dummy() {
    translate([-150, -X_RAIL_W/2, -X_RAIL_H/2]) cube([300, X_RAIL_W, X_RAIL_H]);
    translate([-150, 0, 0]) rotate([0, 90, 0]) color([0.7, 0.7, 0.7]) cylinder(d=16, h=300);
}

module x_slider_block_dummy() {
    translate([-X_BLOCK_L/2, -X_BLOCK_W/2, 0]) cube([X_BLOCK_L, X_BLOCK_W, 10]);
}