// =========================================================================
// 가변 내부 형상 컵 측정 장치 - Z축 관통형 NEMA 17 실시간 애니메이션 모델
// 기성품 스펙 및 도면 치수 반영 (NK4240-L200 / 슬라이딩 애니메이션 구현)
// =========================================================================

$fn = 60;         // 애니메이션의 부드러운 재생을 위해 해상도를 60으로 최적화
TOLERANCE = 0.2;  // 3D 프린팅 끼워맞춤 공차

// --- [1] 도면 치수 파라미터 세팅 (NK4240 NEMA 17 규격 완벽 반영) ---

// 1. 관통형 모터 스펙 (NK4240 - 42각 리니어 모터)
MOTOR_W = 42.0;
MOTOR_PITCH = 31.0;
MOTOR_HOLE_D = 3.5;    
MOTOR_BOSS_D = 22.0;   
MOTOR_BOSS_H = 2.0;    

// 2. Tr8x8 리드스크류 (관통형 축) 규격
SCREW_D = 8.0;         
LEAD_SCREW_L = 250.0;  

// 3. 메인 원통(우물) 및 피스톤 규격
CUP_ID = 100.0;        
CUP_WALL = 6.0;        
CUP_OD = 112.0;        

CUP_H = 180.0;         // 15cm 스트로크 대응 총 고도
CAGE_H = 60.0;         // 하부 배수 공간 및 작업창 높이
FLOOR_H = 10.0;        // 최하단 모터 체결 판 두께

// 4. 방수, 누수 및 작업창 파라미터
LIP_D = 30.0;          
LIP_H = 5.0;           
LEAK_DRAIN_D = 4.0;    
WINDOW_W = 65.0;       

// 5. 배수관 겸 리니어 가이드 & 부싱 규격
GUIDE_PIPE_D = 10.0;   
BUSHING_OD = 12.0;     
BUSHING_H = 8.0;       
DRAIN_RADIUS = 35.0;   
DRAIN_D = 10.0;        
PISTON_H = 25.0;       

// =========================================================================
// [실행부] 애니메이션 조립품 호출
// =========================================================================
assembly();

// =========================================================================
// 시각화 및 검증을 위한 조립품 (Assembly)
// =========================================================================
module assembly() {
    // -----------------------------------------------------------------
    // ★ [슬라이딩 애니메이션 로직]
    // OpenSCAD 특수 변수 $t (0.0 ~ 1.0)를 삼각함수(cos)와 매핑하여 
    // 0mm(최상단)에서 -150mm(최하단) 구간을 부드럽게 무한 왕복 구동시킵니다.
    // -----------------------------------------------------------------
    travel_range = 150.0; // 움직일 총 스트로크 (15cm)
    current_z_pos = -(travel_range / 2) + (travel_range / 2) * cos($t * 360);

    // 1. 외경 112mm 일체형 메인 원통 및 하부 케이지 (투명 뷰)
    color([0.2, 0.5, 0.8, 0.3]) main_cylinder_and_cage();
    
    // 2. 고정 하드웨어 1: 하부에 고정된 NEMA 17 모터 바디
    translate([0, 0, -CUP_H - CAGE_H]) {
        color([0.3, 0.3, 0.3, 1.0]) motor_noncaptive_dummy();
    }
    
    // 3. 고정 하드웨어 2: 바닥판 포켓 홈에 박혀있는 오일리스 부싱 (황동색)
    translate([DRAIN_RADIUS, 0, -CUP_H - CAGE_H + FLOOR_H - BUSHING_H]) {
        bushing_dummy();
    }
    
    // 4. 연동 무빙 컴포넌트 그룹 (피스톤 + 리드스크류 축 + 강성 가이드 배수관)
    // current_z_pos 변수에 의해 통째로 슬라이딩 애니메이션이 적용됩니다.
    translate([0, 0, current_z_pos]) {
        // 4-1. 피스톤
        color([0.7, 0.7, 0.7, 1.0]) piston();
        
        // 4-2. 관통형 스크류 축 (모터 몸체를 뚫고 아래로 왕복 관통)
        translate([0, 0, PISTON_H]) {
            rotate([180, 0, 0])
                color([0.8, 0.8, 0.8, 1.0]) lead_screw_dummy();
        }
        
        // 4-3. 강성 배수 파이프 가이드 (부싱 내벽을 타고 매끄럽게 업/다운)
        translate([DRAIN_RADIUS, 0, PISTON_H]) {
            rotate([180, 0, 0])
                guide_pipe_dummy(length = 220);
        }
    }
}

// =========================================================================
// 컴포넌트 1: 피스톤 (Plunger)
// =========================================================================
module piston() {
    difference() {
        cylinder(d = CUP_ID - (TOLERANCE * 2), h = PISTON_H);
        
        translate([0, 0, -1])
            cylinder(d = SCREW_D + 0.5, h = PISTON_H + 2);
            
        translate([0, 0, PISTON_H - 8])
            cylinder(d = 15.0, h = 9, $fn = 6); 
            
        translate([DRAIN_RADIUS, 0, -1])
            cylinder(d = DRAIN_D + TOLERANCE, h = PISTON_H + 2);
            
        translate([0, 0, 5]) o_ring_groove();
        translate([0, 0, PISTON_H - 9]) o_ring_groove();
    }
}

module o_ring_groove() {
    difference() {
        cylinder(d = CUP_ID + 5, h = 4); 
        translate([0, 0, -1])
            cylinder(d = CUP_ID - 4.0, h = 6); 
    }
}

// =========================================================================
// 컴포넌트 2: 메인 원통 및 하부 모터 고정 케이지
// =========================================================================
module main_cylinder_and_cage() {
    difference() {
        union() {
            difference() {
                union() {
                    translate([0, 0, -5])
                        cylinder(d = CUP_OD + 30, h = 5);
                    translate([0, 0, -CUP_H - CAGE_H])
                        cylinder(d = CUP_OD, h = CUP_H + CAGE_H);
                }
                translate([0, 0, -CUP_H - 0.1])
                    cylinder(d = CUP_ID, h = CUP_H + 0.2);
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H])
                    cylinder(d = CUP_ID, h = CAGE_H - FLOOR_H + 0.1);
            }
            translate([0, 0, -CUP_H - CAGE_H + FLOOR_H])
                cylinder(d = LIP_D, h = LIP_H);
        }
        
        for(a = [45, 135, 225, 315]) {
            rotate([0, 0, a])
                translate([CUP_ID/2 + CUP_WALL + 7.5, 0, -10])
                    cylinder(d = 5.5, h = 20);
        }
        
        translate([-WINDOW_W/2, -CUP_OD/2 - 10, -CUP_H - CAGE_H + FLOOR_H + 5])
            cube([WINDOW_W, CUP_OD + 20, CAGE_H - FLOOR_H - 10]);
            
        translate([0, 0, -CUP_H - CAGE_H - 0.1]) {
            cylinder(d = MOTOR_BOSS_D + TOLERANCE, h = FLOOR_H + LIP_H + 0.2);
            for(x = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) {
                for(y = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) {
                    translate([x, y, -1])
                        cylinder(d = MOTOR_HOLE_D, h = FLOOR_H + 2);
                }
            }
        }
        
        translate([0, 0, -CUP_H - CAGE_H + FLOOR_H + LEAK_DRAIN_D/2]) 
            rotate([0, 90, 0]) 
                cylinder(d = LEAK_DRAIN_D, h = CUP_OD);

        translate([DRAIN_RADIUS, 0, -CUP_H - CAGE_H - 1])
            cylinder(d = GUIDE_PIPE_D + 1.0, h = FLOOR_H + 2); 
            
        translate([0, 0, -CUP_H - CAGE_H + FLOOR_H - BUSHING_H])
            cylinder(d = BUSHING_OD + TOLERANCE, h = BUSHING_H + 0.1);
    }
}

// =========================================================================
// 하드웨어 더미 모듈 (시각화 전용)
// =========================================================================
module bushing_dummy() {
    color([0.8, 0.55, 0.3, 1.0]) {
        difference() {
            cylinder(d = BUSHING_OD, h = BUSHING_H);
            translate([0, 0, -1])
                cylinder(d = GUIDE_PIPE_D, h = BUSHING_H + 2);
        }
    }
}

module guide_pipe_dummy(length = 200) {
    color([0.65, 0.67, 0.68, 1.0]) {
        difference() {
            cylinder(d = GUIDE_PIPE_D, h = length);
            translate([0, 0, -1])
                cylinder(d = GUIDE_PIPE_D - 1.6, h = length + 2); 
        }
    }
}

module lead_screw_dummy() {
    cylinder(d=SCREW_D, h=LEAD_SCREW_L);
}

module motor_noncaptive_dummy() {
    difference() {
        union() {
            translate([-MOTOR_W/2, -MOTOR_W/2, -40])
                cube([MOTOR_W, MOTOR_W, 40]);
            cylinder(d = MOTOR_BOSS_D, h = MOTOR_BOSS_H);
        }
        translate([0, 0, -45]) cylinder(d = SCREW_D + 2, h = 50);
        for(x = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) {
            for(y = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) {
                translate([x, y, -10]) cylinder(d = 3, h = 15);
            }
        }
    }
}