// =========================================================================
// [갠트리 가변 내부 형상 측정 시스템] 무빙 원통 구동 범위 최종 교정판 (스피커 형상 수정본)
// 기준 원점 (0,0,0) = X축 최좌측 상태의 컵 원통 윗면 중심 및 피스톤 플랫 일치
// 교정 완료: 스피커 더미가 관통 파이프처럼 보이던 기하학적 에러 완벽 수정 (후면 마그넷 폐쇄)
// =========================================================================

$fn = 40; 
GLOBAL_TOLERANCE = 0.2;

// --- [1] 하부 기성품 및 원통 파라미터 세팅 ---
X_RAIL_LEN = 350.0;  // 350mm 기성품 레일 가이드 규격 고정
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
SHAFT_D = 12.0;          
HUB_WALL = 4.0;          
LOWER_HUB_H = 40.0;      
POCKET_DEPTH = 25.0;     

// --- [3] STS3032 스마트 서보 및 계측기 스펙 파라미터 ---
SERVO_3032_L = 45.5; SERVO_3032_W = 24.7; SERVO_3032_H = 37.0; 
SERVO_HORN_D = 25.0;     
SERVO_HORN_H = 6.0;      
HORN_PCD = 18.0;         

UPPER_BRKT_H = 8.0;       
X_POS_MEASURE = 165.0;   // 파란 가로보 X방향 중앙: (X_M+PF + X_R) / 2 = (80+250)/2

// --- [4] 글로벌 2020 프레임 경계 파라미터 ---
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

// =========================================================================
// 17단계 시퀀스 애니메이션 (전체 작동 과정)
// ★ STACK_ORDER만 바꾸면 전체 애니메이션이 자동 조정됨 ★
// 예: [0,5,2]=1→6→3번  [1,3,4]=2→4→5번  [0,0,2]=1번×2+3번
// =========================================================================
STACK_ORDER = [0, 5, 2];  // ← 여기만 바꿀 것!

// ── 링 데이터 (전역 상수) ──
RING_IDS = [20, 32, 44, 56, 68, 80];
RING_CLRS = [[1,0,0], [1,0.6,0], [1,1,0], [0,1,0], [0,0,1], [0.5,0,0.8]];

// ── STACK_ORDER에서 파생 ──
S0 = STACK_ORDER[0]; S1 = STACK_ORDER[1]; S2 = STACK_ORDER[2];
R0 = -S0 * 60; R1 = -S1 * 60; R2 = -S2 * 60;
R_PREV = -((S0 + 5) % 6) * 60;  // 시작 위치: S0 이전 슬롯

ANIM_N = 17;
anim_phase = min(floor($t * ANIM_N), ANIM_N - 1);
anim_pt = ($t * ANIM_N) - anim_phase;
anim_s = (1 - cos(anim_pt * 180)) / 2;  // ease-in-out

// ── Z축 피스톤 위치 (0=최상위, 음수=하강) ──
Z_MOVE =
    anim_phase == 0 ? 0 :
    anim_phase == 1 ? -10 * anim_s :
    anim_phase == 2 ? -10 :
    anim_phase == 3 ? -10 - 10 * anim_s :
    anim_phase == 4 ? -20 :
    anim_phase == 5 ? -20 - 10 * anim_s :
    (anim_phase >= 6 && anim_phase <= 11) ? -30 :
    anim_phase == 12 ? -30 + 10 * anim_s :
    anim_phase == 13 ? -20 :
    anim_phase == 14 ? -20 + 10 * anim_s :
    anim_phase == 15 ? -10 :
    anim_phase == 16 ? -10 + 10 * anim_s : 0;

// ── X축 원통 이동 (0=원점, 165=측정 위치) ──
X_MOVE =
    (anim_phase <= 5) ? 0 :
    anim_phase == 6 ? 165 * anim_s :
    (anim_phase >= 7 && anim_phase <= 10) ? 165 :
    anim_phase == 11 ? 165 * (1 - anim_s) : 0;

// ── 카트리지 회전 각도 (phase 0: 이전 슬롯→S0 회전으로 시작) ──
REV_ANG =
    anim_phase == 0 ? R_PREV + (R0 - R_PREV) * anim_s :
    anim_phase == 1 ? R0 :
    anim_phase == 2 ? R0 + (R1 - R0) * anim_s :
    anim_phase == 3 ? R1 :
    anim_phase == 4 ? R1 + (R2 - R1) * anim_s :
    (anim_phase >= 5 && anim_phase <= 12) ? R2 :
    anim_phase == 13 ? R2 + (R1 - R2) * anim_s :
    anim_phase == 14 ? R1 :
    anim_phase == 15 ? R1 + (R0 - R1) * anim_s : R0;

// ── 수위 (개념적, mm) ──
WATER_H =
    anim_phase == 7 ? 10 * anim_s :
    anim_phase == 8 ? 10 + 10 * anim_s :
    anim_phase == 9 ? 20 + 10 * anim_s :
    anim_phase == 10 ? 30 * (1 - anim_s) : 0;

// ── 적재 추적 (STACK_ORDER 기반 자동 계산) ──
DEP_S0 = (anim_phase >= 2) ? 1 : 0;
DEP_S1 = (anim_phase >= 4 && anim_phase < 15) ? 1 : 0;
DEP_S2 = (anim_phase >= 6 && anim_phase < 13) ? 1 : 0;
DEPLETED = [for(i = [0:5])
    (i == S0 ? DEP_S0 : 0) +
    (i == S1 ? DEP_S1 : 0) +
    (i == S2 ? DEP_S2 : 0)
];

// ── 슬롯별 독립 링 드롭 오프셋 (내려간 상태 유지, STACK_ORDER 기반) ──
DROP_S0 = (anim_phase == 0) ? 0 : (anim_phase == 1) ? Z_MOVE : (anim_phase >= 2 && anim_phase <= 15) ? -10 : (anim_phase == 16) ? Z_MOVE : 0;
DROP_S1 = (anim_phase <= 2) ? 0 : (anim_phase == 3) ? Z_MOVE + 10 : (anim_phase >= 4 && anim_phase <= 13) ? -10 : (anim_phase == 14) ? Z_MOVE + 10 : 0;
DROP_S2 = (anim_phase <= 4) ? 0 : (anim_phase == 5) ? Z_MOVE + 20 : (anim_phase >= 6 && anim_phase <= 11) ? -10 : (anim_phase == 12) ? Z_MOVE + 20 : 0;
DROPS = [for(i = [0:5])
    (i == S0 ? DROP_S0 : 0) +
    (i == S1 ? DROP_S1 : 0) +
    (i == S2 ? DROP_S2 : 0)
];    

// =========================================================================
// [실행부] 메인 시스템 대조립
// =========================================================================
main_system_assembly();

module main_system_assembly() {
    aluminum_profile_frame();
    upper_fixed_base_plate();
    translate([-REVOLVER_PCD/2, 0, 0]) teflon_washer_dummy();
    translate([-REVOLVER_PCD/2, 0, 0]) upper_servo_frame_assembly();
    translate([-REVOLVER_PCD/2, 0, WASHER_T]) rotate([0, 0, REV_ANG]) acryl_pipe_revolver_assembly(DEPLETED, DROPS);
    fluidic_control_system_assembly();
    translate([-260, -165, Z_BOT + PF]) water_reservoir_tank();
    
    // 계측 브래킷 모듈 배치
    translate([X_POS_MEASURE, 0, Z_TOP - PF]) acoustic_measurement_module();

    // ---------------------------------------------------------------------
    // 하부 이동 구조체 그룹
    // ---------------------------------------------------------------------
    color([0.4, 0.4, 0.4]) translate([0, -Y_OFFSET, -252 - 10 - X_RAIL_H/2]) x_stage_rail_dummy();
    color([0.4, 0.4, 0.4]) translate([0, Y_OFFSET, -252 - 10 - X_RAIL_H/2]) x_stage_rail_dummy();

    translate([X_MOVE, 0, 0]) {
        color([0.2, 0.2, 0.2]) translate([0, -Y_OFFSET, -252 - 10]) x_slider_block_dummy();
        color([0.2, 0.2, 0.2]) translate([0, Y_OFFSET, -252 - 10]) x_slider_block_dummy();
        color([0.2, 0.6, 0.3]) translate([0, 0, -252]) h_bridge_adapter_plate();
        z_cylinder_and_cage();
        translate([-DRAIN_RADIUS, 0, -CUP_H - CAGE_H + FLOOR_H - BUSHING_H]) bushing_dummy();
        translate([0, 0, -CUP_H - CAGE_H]) color([0.1, 0.1, 0.1]) z_motor_dummy();
        translate([0, 0, Z_MOVE]) z_moving_parts_assembly();

        // ── 적재된 링 (STACK_ORDER 기반 자동 색상/ID) ──
        if (DEP_S0 == 1) color(RING_CLRS[S0], 0.9) translate([0,0,Z_MOVE])
            difference() { cylinder(d=ACRYL_ID-0.2,h=10); translate([0,0,-0.1]) cylinder(d=RING_IDS[S0],h=10.2); }
        if (DEP_S1 == 1) color(RING_CLRS[S1], 0.9) translate([0,0,Z_MOVE+10])
            difference() { cylinder(d=ACRYL_ID-0.2,h=10); translate([0,0,-0.1]) cylinder(d=RING_IDS[S1],h=10.2); }
        if (DEP_S2 == 1) color(RING_CLRS[S2], 0.9) translate([0,0,Z_MOVE+20])
            difference() { cylinder(d=ACRYL_ID-0.2,h=10); translate([0,0,-0.1]) cylinder(d=RING_IDS[S2],h=10.2); }

        // ── 수위 (개념적 표현) ──
        if (WATER_H > 0.1) color([0.2,0.5,1.0,0.5]) translate([0,0,Z_MOVE])
            cylinder(d=CUP_ID - 2, h=WATER_H);
    }
}

// =========================================================================
// [데이터시트 기반 정밀 재설계] 4인치 Low Frequency Driver 실물 더미
// Mounting: OD=106  PCD=116  Cutout=102  Depth=55mm
// z=0 = 전면 플랜지면 (콘 쪽),  +Z 방향으로 마그넷 연장
// =========================================================================
module speaker_4inch_dummy() {
    OD=106; CUT=102; PCD=116; DEPTH=55; FT=3;  // FT=3 (도면 "3.0")
    CONE_H=22; MAG_D=56; MAG_H=DEPTH-FT-CONE_H;
    FW=120; FCR=10;  // 사각 플랜지 한변 120mm, 코너 R=10mm

    // ── 라운드 사각형 전면 플랜지 (도면 기준) ──
    color([0.13,0.13,0.13]) difference() {
        hull() {
            for(sx=[-1,1]) for(sy=[-1,1])
                translate([sx*(FW/2-FCR), sy*(FW/2-FCR), 0])
                    cylinder(r=FCR, h=FT);
        }
        translate([0,0,-0.1]) cylinder(d=CUT-4, h=FT+0.2);
        // 5.0×6.0 슬롯홀 4개 (PCD 116, 45° 배치)
        for(a=[45,135,225,315]) rotate([0,0,a])
            translate([PCD/2, 0, -0.1]) hull() {
                translate([-0.5, 0, 0]) cylinder(d=5, h=FT+0.2);
                translate([0.5, 0, 0]) cylinder(d=5, h=FT+0.2);
            }
    }

    // ── 바스켓 프레임 (통풍 슬롯 8개) ──
    color([0.11,0.11,0.11]) translate([0,0,FT]) difference() {
        cylinder(d1=OD-4, d2=MAG_D+6, h=CONE_H);
        translate([0,0,-0.1]) cylinder(d1=OD-8, d2=MAG_D+2, h=CONE_H-2);
        for(a=[22.5:45:360]) rotate([0,0,a])
            translate([18,-5,3]) cube([30,10,CONE_H-6]);
    }

    // ── 종이 진동판 콘 ──
    color([0.28,0.25,0.22]) translate([0,0,1]) difference() {
        cylinder(d1=CUT-6, d2=28, h=CONE_H-2);
        translate([0,0,-0.2]) cylinder(d1=CUT-8, d2=26, h=CONE_H-2);
    }

    // ── 더스트 캡 ──
    color([0.15,0.15,0.15]) translate([0,0,CONE_H-3]) difference() {
        scale([1,1,0.4]) sphere(d=30);
        scale([1,1,0.4]) sphere(d=28);
        translate([-20,-20,-20]) cube([40,40,20]);
    }

    // ── 마그넷 어셈블리 (요크 + 자석 + 후면 플레이트) ──
    color([0.18,0.18,0.18]) translate([0,0,FT+CONE_H]) {
        cylinder(d=MAG_D+6, h=3);
        translate([0,0,3]) cylinder(d=MAG_D, h=MAG_H-6);
        translate([0,0,MAG_H-3]) cylinder(d=MAG_D+4, h=3);
    }

    // ── 단자 터미널 ──
    color([0.6,0.6,0.6]) {
        translate([-12,MAG_D/2-3,DEPTH-3]) cube([6,3,3]);
        translate([6,MAG_D/2-3,DEPTH-3]) cube([6,3,3]);
    }
}

// =========================================================================
// [스펙시트 기반 정밀 재설계] Earthworks M50 측정 마이크 실물 더미
// Dimensions: 229 × ø22 mm  |  팁 프로브: ø7 mm
// z=0 = 팁 선단,  +Z 방향으로 본체 (XLR) 연장
// =========================================================================
module m50_mic_dummy() {
    BD=22; TD=7;
    TIP_L=30; TAPER_L=20; BODY_L=155; XLR_L=24;  // 합계 229mm

    color([0.3,0.3,0.3])    translate([0,0,-1])            cylinder(d=TD+0.5, h=1);
    color([0.82,0.82,0.82])                                cylinder(d=TD, h=TIP_L);
    color([0.82,0.82,0.82]) translate([0,0,TIP_L])         cylinder(d1=TD, d2=BD, h=TAPER_L);
    color([0.80,0.80,0.80]) translate([0,0,TIP_L+TAPER_L]) cylinder(d=BD, h=BODY_L);
    color([0.25,0.25,0.25]) translate([0,0,TIP_L+TAPER_L+BODY_L]) cylinder(d=BD, h=XLR_L);
    color([0.15,0.15,0.15]) translate([0,0,229-0.5])
        for(a=[0,120,240]) rotate([0,0,a]) translate([5,0,0]) cylinder(d=2, h=1);
}

// =========================================================================
// [도면 기반 재설계] 음향 계측 통합 브래킷 + 기성품 배치
// 스피커 사각 플랜지(120×120 R=10) 대응, 라운드사각 슈라우드
// 보 하면(z=0) 기준 하향 매달림, 3D 프린팅 단일 파트
// =========================================================================
module acoustic_measurement_module() {
    TOL = 0.3;

    // ── 4인치 스피커 데이터시트 치수 ──
    SPK_OD=106;  SPK_CUT=102;  SPK_PCD=116;
    SPK_DEPTH=55;  SPK_HOLE=5;  SPK_FT=3;

    // ── M50 마이크 ──
    MIC_D=22;  MIC_TD=7;

    // ── 급수관 ──
    TUBE_OD=8;

    // ── 브래킷 설계 파라미터 ──
    PT   = 10;       // 상부 볼팅 판재 두께
    WALL = 5;        // 슈라우드 벽 두께

    // ── 스피커 사각 플랜지 치수 ──
    FW=120;  FCR=10;                                  // 사각 플랜지 한변/코너R
    PKT_W = FW + TOL*2;   PKT_CR = FCR + TOL;        // 포켓 120.6×120.6, R=10.3
    SHR_W = PKT_W + WALL*2; SHR_CR = PKT_CR + WALL;  // 슈라우드 130.6×130.6, R=15.3
    SH_EXT = SHR_W / 2;                              // 가이드 앵커용 반폭 (≈65.3)

    // ── 좌표 산출 ──
    SPK_Z  = -PT - SPK_DEPTH;       // -65  (스피커 플랜지 위치)
    SH_BOT = SPK_Z - WALL;          // -70  (슈라우드 하단)
    SH_H   = -PT - SH_BOT;          // 60   (슈라우드 높이)

    // ── 마이크 피벗 (슈라우드 하단 — 스피커 간섭 회피) ──
    MP_Z = SH_BOT;                                    // -70

    // ── 마이크 목표: 팁 → 원통 중앙(y=0), 윗면+5mm(z_local=-180) ──
    MIC_ANG  = 35;                                    // 사선 각도 (스피커 우회)
    MIC_PRO  = (MP_Z + 180) / cos(MIC_ANG);           // ≈ 134mm 돌출
    MIC_Y    = -MIC_PRO * sin(MIC_ANG);               // ≈ -77

    // ── 급수관 목표: 팁 → y=35, z_local=-165 ──
    TP_Z = MP_Z;
    TUBE_ANG = atan((65 - 35) / (TP_Z + 165));        // ≈ 17.4°
    TUBE_Y   = 35 + (TP_Z + 165) * tan(TUBE_ANG);     // ≈ 65
    // 노즐 연장: 컵 윗면+30mm(z_local=-155)까지 가이드
    NOZZLE_EXIT_Z = -155;
    NOZZLE_AXIS_L = (TP_Z - NOZZLE_EXIT_Z) / cos(TUBE_ANG);

    // -----------------------------------------------------------------
    // [1] 3D 프린팅 일체형 브래킷 바디
    // -----------------------------------------------------------------
    color([0.25, 0.55, 0.55, 0.85]) difference() {
        union() {
            // ① 상부 볼팅 판재 (보 하면 밀착, 180×70×10mm)
            translate([-90, -35, -PT]) cube([180, 70, PT]);

            // ② 스피커 라운드사각 슈라우드 (플랜지 형상에 맞춤)
            translate([0, 0, SH_BOT]) hull() {
                for(sx=[-1,1]) for(sy=[-1,1])
                    translate([sx*(SHR_W/2-SHR_CR), sy*(SHR_W/2-SHR_CR), 0])
                        cylinder(r=SHR_CR, h=SH_H);
            }

            // ③ 마이크 가이드 브릿지 (슈라우드 벽 → 가이드 출구)
            hull() {
                translate([0, -SH_EXT, MP_Z-15]) cylinder(d=25, h=30);
                translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0])
                    translate([0,0,-20]) cylinder(d=MIC_D+14, h=65);
            }

            // ③-b 마이크 클램프 귀 (가이드 원통 -Y쪽 바깥면, 슬릿 양쪽 ±X)
            translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0]) {
                // 좌우 귀 탭 (원통 바깥면 y=-18에서 10mm 하방 돌출)
                translate([0.75, -(18+10), 5]) cube([10, 10, 25]);
                translate([-(0.75+10), -(18+10), 5]) cube([10, 10, 25]);
            }

            // ④ 급수관 가이드 상부 브릿지 (슈라우드 → 가이드 입구)
            hull() {
                translate([0, SH_EXT, TP_Z-10]) cylinder(d=18, h=20);
                translate([0, TUBE_Y, TP_Z]) rotate([-TUBE_ANG,0,0])
                    translate([0,0,-15]) cylinder(d=TUBE_OD+14, h=55);
            }

            // ⑤ 급수관 연장 노즐 (컵 윗면+3cm까지 사선 가이드)
            translate([0, TUBE_Y, TP_Z]) rotate([-TUBE_ANG,0,0])
                translate([0, 0, -NOZZLE_AXIS_L]) cylinder(d=TUBE_OD+6, h=NOZZLE_AXIS_L-15);
        }

        // ── 감산 가공부 ──

        // ① M5 볼트 관통 (보 T슬롯 체결, X방향 4개)
        for(x = [-75, -40, 40, 75]) {
            translate([x, 0, -PT-1]) cylinder(d=5.5, h=PT+2);
            translate([x, 0, -PT-1]) cylinder(d=10, h=4);
        }

        // ② 음파 방사 개구 (하단 벽 관통, d=96 — 플랜지 립 확보)
        translate([0, 0, SH_BOT-1]) cylinder(d=96, h=WALL+1);

        // ③ 스피커 사각 포켓 (플랜지 레벨~상단, 라운드사각 120.6×120.6)
        //    ②과의 차이가 플랜지를 받치는 립 형성
        translate([0, 0, SPK_Z]) hull() {
            for(sx=[-1,1]) for(sy=[-1,1])
                translate([sx*(PKT_W/2-PKT_CR), sy*(PKT_W/2-PKT_CR), 0])
                    cylinder(r=PKT_CR, h=SPK_DEPTH+5);
        }

        // ④ 스피커 고정 나사 (PCD 116, M5 관통, 4축)
        for(a = [45, 135, 225, 315]) rotate([0,0,a])
            translate([SPK_PCD/2, 0, SH_BOT-1])
                cylinder(d=SPK_HOLE+0.5, h=WALL+SPK_FT+2);

        // ⑤ 배선 관통 (상부, 마그넷 윗면 → 판재)
        translate([0, 0, SPK_Z+SPK_DEPTH-2]) cylinder(d=40, h=PT+5);

        // ⑥ 마이크 스텝 보어
        translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0]) {
            cylinder(d=MIC_TD+TOL*2, h=500, center=true);
            translate([0,0,-40]) cylinder(d=MIC_D+TOL*2, h=250);
        }

        // ⑥-b 클램프 슬릿 (가이드 원통 전체 높이 절개)
        //    z: -22~+47 (원통 z=-20~+45 전구간 + 여유)
        translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0])
            translate([-0.75, -30, -22]) cube([1.5, 31, 69]);

        // ⑥-c 클램프 볼트홀 (M4, X방향, 귀 중심 관통 — 마이크 바깥쪽)
        translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0])
            translate([0, -23, 17.5]) rotate([0,90,0])
                cylinder(d=4.3, h=40, center=true);

        // ⑦ 급수관 관통 보어
        translate([0, TUBE_Y, TP_Z]) rotate([-TUBE_ANG,0,0])
            cylinder(d=TUBE_OD+TOL, h=500, center=true);

        // ⑧ z≥0 클리핑 (보 영역 침범 방지)
        translate([-80, -120, 0]) cube([160, 240, 80]);
    }

    // -----------------------------------------------------------------
    // [2] 4인치 스피커 실물 더미 배치 (콘 하방)
    // -----------------------------------------------------------------
    translate([0, 0, SPK_Z]) speaker_4inch_dummy();

    // -----------------------------------------------------------------
    // [3] Earthworks M50 마이크 실물 더미 배치
    // -----------------------------------------------------------------
    translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0])
        translate([0, 0, -MIC_PRO]) m50_mic_dummy();

    // -----------------------------------------------------------------
    // [4] 실리콘 급수 튜브 (노즐 끝+5mm ~ 가이드 상단+10mm)
    // -----------------------------------------------------------------
    TUBE_EXIT = 50;  // 축 z=+40(가이드 상단)+10mm 돌출
    color([0.85, 0.85, 0.85, 0.35])
    translate([0, TUBE_Y, TP_Z]) rotate([-TUBE_ANG,0,0])
        translate([0, 0, -(NOZZLE_AXIS_L+5)]) difference() {
            cylinder(d=TUBE_OD, h=NOZZLE_AXIS_L+5+TUBE_EXIT);
            translate([0,0,-1]) cylinder(d=TUBE_OD-2, h=NOZZLE_AXIS_L+5+TUBE_EXIT+2);
    }
}

// =========================================================================
// 기성품 350mm X축 슬라이드 레일 가이드 모델
// =========================================================================
module x_stage_rail_dummy() { 
    RAIL_START_X = (X_R + PF) - X_RAIL_LEN; 
    translate([RAIL_START_X, -X_RAIL_W/2, -X_RAIL_H/2]) cube([350, X_RAIL_W, X_RAIL_H]); 
    translate([RAIL_START_X, 0, 0]) rotate([0, 90, 0]) color([0.7, 0.7, 0.7]) cylinder(d=16, h=350); 
}

// =========================================================================
// 하단 X축 레일보 고정형 유체 제어 장치 및 순환 배관
// =========================================================================
module fluidic_control_system_assembly() {
    PUMP_X = -120; PUMP_Y = Y_OFFSET; PUMP_Z = Z_RAIL + PF; 
    translate([PUMP_X, PUMP_Y, PUMP_Z]) {
        color([0.2, 0.7, 0.9]) cylinder(d=45, h=30);
        color([0.15, 0.15, 0.15]) translate([-21, -21, 30]) cube([42, 42, 40]); 
        color([0.6, 0.6, 0.6]) { translate([-12, -22, 15]) rotate([90, 0, 0]) cylinder(d=5, h=8); translate([12, -22, 15]) rotate([90, 0, 0]) cylinder(d=5, h=8); }
        color([0.5, 0.5, 0.5]) translate([-25, -20, 0]) { difference() { cube([50, 40, 4]); translate([8, 8, -1]) cylinder(d=4.5, h=6); translate([42, 8, -1]) cylinder(d=4.5, h=6); } }
    }

    VALVE_X = -190; VALVE_Y = Y_OFFSET; VALVE_Z = Z_RAIL - 30; 
    translate([VALVE_X, VALVE_Y, VALVE_Z]) {
        color([0.7, 0.5, 0.2]) cube([30, 40, 30]); 
        color([0.1, 0.1, 0.1]) translate([0, 5, 30]) cube([30, 30, 25]); 
        color([0.6, 0.6, 0.6]) { translate([15, -8, 15]) rotate([90, 0, 0]) cylinder(d=8, h=8); translate([15, 48, 15]) rotate([90, 0, 0]) cylinder(d=8, h=8); }
        color([0.4, 0.4, 0.4]) translate([-5, 5, 25]) cube([40, 30, 5]);
    }

    color([0.9, 0.9, 0.9, 0.5]) { 
        tube_curve([-150, Y_OFFSET + 30, -420], [-150, Y_OFFSET + 30, -320], 6);
        tube_curve([-150, Y_OFFSET + 30, -320], [PUMP_X - 12, PUMP_Y - 22, PUMP_Z + 15], 6);
        // 급수관: 펌프 → 프레임 뒤쪽(Y_B)으로 돌아서 → 브래킷 가이드 상단 출구
        tube_bezier(
            [PUMP_X + 12, PUMP_Y - 22, PUMP_Z + 15],  // P0: 펌프 출구
            [PUMP_X + 12, Y_B + 30, PUMP_Z + 50],      // P1: 뒤쪽으로 올라가는 접선
            [X_POS_MEASURE, Y_B + 30, Z_TOP],           // P2: 브래킷 뒤쪽 상단 접선
            [X_POS_MEASURE, 80, 163],                    // P3: 가이드 상단 +10mm 출구점
            6, 30);
        tube_curve([X_MOVE - DRAIN_RADIUS, 0, Z_MOVE - 260], [(X_MOVE - DRAIN_RADIUS + VALVE_X)/2, 40, -300], 8);
        tube_curve([(X_MOVE - DRAIN_RADIUS + VALVE_X)/2, 40, -300], [VALVE_X + 15, VALVE_Y - 8, VALVE_Z + 15], 8);
        tube_curve([VALVE_X + 15, VALVE_Y + 48, VALVE_Z + 15], [VALVE_X + 15, VALVE_Y + 48, -410], 8);
    }
}

module tube_curve(start, end, d) {
    color([0.9, 0.9, 0.9, 0.3]) hull() {
        translate(start) sphere(d=d);
        translate(end) sphere(d=d);
    }
}

// 3차 베지어 곡선 튜브 (4개 제어점, N 세그먼트)
module tube_bezier(P0, P1, P2, P3, d, N=20) {
    color([0.9, 0.9, 0.9, 0.3])
    for(i = [0 : N-1]) {
        t0 = i / N;
        t1 = (i + 1) / N;
        // 드 카스텔자우 3차 베지어
        a0 = (1-t0)*(1-t0)*(1-t0);
        b0 = 3*(1-t0)*(1-t0)*t0;
        c0 = 3*(1-t0)*t0*t0;
        d0 = t0*t0*t0;
        a1 = (1-t1)*(1-t1)*(1-t1);
        b1 = 3*(1-t1)*(1-t1)*t1;
        c1 = 3*(1-t1)*t1*t1;
        d1 = t1*t1*t1;
        pt0 = [a0*P0[0]+b0*P1[0]+c0*P2[0]+d0*P3[0],
               a0*P0[1]+b0*P1[1]+c0*P2[1]+d0*P3[1],
               a0*P0[2]+b0*P1[2]+c0*P2[2]+d0*P3[2]];
        pt1 = [a1*P0[0]+b1*P1[0]+c1*P2[0]+d1*P3[0],
               a1*P0[1]+b1*P1[1]+c1*P2[1]+d1*P3[1],
               a1*P0[2]+b1*P1[2]+c1*P2[2]+d1*P3[2]];
        hull() {
            translate(pt0) sphere(d=d);
            translate(pt1) sphere(d=d);
        }
    }
}

// =========================================================================
// 2020 알루미늄 프로파일 전체 골조 프레임 모듈
// =========================================================================
module aluminum_profile_frame() { 
    color([0.75, 0.75, 0.75]) { 
        translate([X_L, Y_B, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); translate([X_L, Y_F, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); 
        translate([X_M, Y_B, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); translate([X_M, Y_F, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); 
        translate([X_R, Y_B, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); translate([X_R, Y_F, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); 
    } 
    color([0.65, 0.65, 0.65]) { 
        translate([X_L + PF, Y_B, Z_BOT]) cube([X_R - X_L - PF, PF, PF]); translate([X_L + PF, Y_F, Z_BOT]) cube([X_R - X_L - PF, PF, PF]); 
        translate([X_L, Y_F + PF, Z_BOT]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_R, Y_F + PF, Z_BOT]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_M, Y_F + PF, Z_BOT]) cube([PF, Y_B - Y_F - PF, PF]); 
    } 
    color([0.8, 0.8, 0.8]) { 
        translate([X_L, -Y_OFFSET - PF/2, Z_RAIL]) cube([X_R - X_L + PF, PF, PF]); translate([X_L, Y_OFFSET - PF/2, Z_RAIL]) cube([X_R - X_L + PF, PF, PF]); 
        translate([X_L, Y_F + PF, Z_RAIL]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_M, Y_F + PF, Z_RAIL]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_R, Y_F + PF, Z_RAIL]) cube([PF, Y_B - Y_F - PF, PF]); 
    } 
    color([0.7, 0.7, 0.7]) { 
        translate([X_L + PF, Y_B, Z_MID]) cube([X_M - X_L - PF, PF, PF]); translate([X_L + PF, Y_F, Z_MID]) cube([X_M - X_L - PF, PF, PF]); 
        translate([X_L, Y_F + PF, Z_MID]) cube([PF, Y_B - Y_F - PF, PF]); translate([-85, Y_F + PF, Z_MID]) cube([PF, Y_B - Y_F - PF, PF]); 
    } 
    color([0.75, 0.75, 0.75]) { 
        translate([X_L + PF, Y_B, Z_TOP - PF]) cube([X_R - X_L - PF, PF, PF]); translate([X_L + PF, Y_F, Z_TOP - PF]) cube([X_R - X_L - PF, PF, PF]); 
        translate([X_L, Y_F + PF, Z_TOP - PF]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_M, Y_F + PF, Z_TOP - PF]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_R, Y_F + PF, Z_TOP - PF]) cube([PF, Y_B - Y_F - PF, PF]); 
    } 
    color([0.65, 0.65, 0.65]) { 
        translate([X_L + PF, -50, Z_TOP - PF]) cube([X_M - X_L - PF, PF, PF]); translate([X_L + PF, 20, Z_TOP - PF]) cube([X_M - X_L - PF, PF, PF]); 
    } 
    // 측정 브래킷 장착용 가로보 (X방향, Y=0 중심, 파란색)
    color([0.75, 0.75, 0.75]) { 
        translate([X_M + PF, -PF/2, Z_TOP - PF]) cube([X_R - X_M - PF, PF, PF]); 
    } 
}

// =========================================================================
// 하부 고정 서브 시스템 하우징 모듈 그룹
// =========================================================================
module upper_fixed_base_plate() { color([0.5, 0.5, 0.5, 0.5]) { difference() { translate([X_L, Y_F, -TOP_PLATE_H]) cube([(X_M + PF) - X_L, (Y_B + PF) - Y_F, TOP_PLATE_H]); translate([X_L - 1, Y_B - 1, -TOP_PLATE_H - 1]) cube([PF + 1 + GLOBAL_TOLERANCE, PF + 1 + GLOBAL_TOLERANCE, TOP_PLATE_H + 2]); translate([X_L - 1, Y_F - 1, -TOP_PLATE_H - 1]) cube([PF + 1 + GLOBAL_TOLERANCE, PF + 1 + GLOBAL_TOLERANCE, TOP_PLATE_H + 2]); translate([X_M - GLOBAL_TOLERANCE, Y_B - 1, -TOP_PLATE_H - 1]) cube([PF + 1 + GLOBAL_TOLERANCE, PF + 1 + GLOBAL_TOLERANCE, TOP_PLATE_H + 2]); translate([X_M - GLOBAL_TOLERANCE, Y_F - 1, -TOP_PLATE_H - 1]) cube([PF + 1 + GLOBAL_TOLERANCE, PF + 1 + GLOBAL_TOLERANCE, TOP_PLATE_H + 2]); translate([0, -(CUP_OD + GLOBAL_TOLERANCE)/2, -TOP_PLATE_H - 1]) cube([CARTRIDGE_OD, CUP_OD + GLOBAL_TOLERANCE, TOP_PLATE_H + 2]); translate([0, 0, -TOP_PLATE_H - 1]) cylinder(d=CUP_OD + GLOBAL_TOLERANCE, h=TOP_PLATE_H + 2); translate([-REVOLVER_PCD/2, 0, -TOP_PLATE_H - 1]) cylinder(d=36, h=TOP_PLATE_H + 2); } } }
module upper_servo_frame_assembly() { color([0.4, 0.4, 0.4, 0.8]) translate([0, 0, SUPPORT_PILLAR_H]) { difference() { translate([-35, -60, 0]) cube([70, 110, UPPER_BRKT_H]); translate([-SERVO_3032_L/2, -SERVO_3032_W/2, -1]) cube([SERVO_3032_L, SERVO_3032_W, UPPER_BRKT_H + 2]); for(x = [-(SERVO_3032_L+9)/2, (SERVO_3032_L+9)/2]) { for(y = [-8, 8]) { translate([x, y, -1]) cylinder(d=2.5, h=UPPER_BRKT_H + 2); } } for(x = [-20, 20]) { translate([x, -40, -1]) cylinder(d=4.5, h=UPPER_BRKT_H + 2); translate([x, 30, -1]) cylinder(d=4.5, h=UPPER_BRKT_H + 2); } } } translate([0, 0, SUPPORT_PILLAR_H - 10]) { color([0.15, 0.15, 0.15]) { translate([-SERVO_3032_L/2, -SERVO_3032_W/2, 0]) cube([SERVO_3032_L, SERVO_3032_W, SERVO_3032_H]); translate([-(SERVO_3032_L+15)/2, -SERVO_3032_W/2, 10]) cube([SERVO_3032_L+15, SERVO_3032_W, 2.5]); } color([1, 0.4, 0]) translate([-SERVO_3032_L/2, -SERVO_3032_W/2, 12.5]) cube([SERVO_3032_L, SERVO_3032_W, 10]); } translate([0, 0, 166]) color([0.85, 0.85, 0.85]) { difference() { cylinder(d=SERVO_HORN_D, h=SERVO_HORN_H); translate([0, 0, -0.1]) cylinder(d=4, h=SERVO_HORN_H + 0.2); for(a=[0:90:270]) { rotate([0, 0, a]) translate([HORN_PCD/2, 0, -1]) cylinder(d=2.0, h=8); } } } color([0.6, 0.6, 0.6]) translate([-PF/2, -PF/2, 20]) cube([PF, PF, 146]); }
module acryl_pipe_revolver_assembly(depleted=[0,0,0,0,0,0], drops=[0,0,0,0,0,0]) { translate([0, 0, 0]) color([0.2, 0.2, 0.2]) difference() { union() { cylinder(d=HUB_D + 15, h=LOWER_HUB_H); for(a = [0 : 60 : 359]) { rotate([0, 0, a]) { translate([HUB_D/2, -7, 0]) cube([REVOLVER_PCD/2 - HUB_D/2, 14, LOWER_HUB_H - 5]); translate([REVOLVER_PCD/2, 0, 0]) cylinder(d=ACRYL_OD + (HUB_WALL * 2), h=LOWER_HUB_H); } } } translate([0, 0, -1]) cylinder(d=SHAFT_D, h=LOWER_HUB_H + 2); translate([-(PF+GLOBAL_TOLERANCE)/2, -(PF+GLOBAL_TOLERANCE)/2, -TOP_PLATE_H - 1]) cube([PF + GLOBAL_TOLERANCE, PF + GLOBAL_TOLERANCE, LOWER_HUB_H + TOP_PLATE_H + 2]); rotate([0, 90, 0]) translate([-20, 0, 0]) cylinder(d=4.2, h=HUB_D); for(a = [0 : 60 : 359]) { rotate([0, 0, a]) translate([REVOLVER_PCD/2, 0, -1]) { translate([0, 0, LOWER_HUB_H - POCKET_DEPTH + 1]) cylinder(d=ACRYL_OD + GLOBAL_TOLERANCE, h=POCKET_DEPTH + 0.1); cylinder(d=CUP_ID + 0.5, h=LOWER_HUB_H + 2); } } } translate([0, 0, 145]) color([0.2, 0.2, 0.2]) difference() { union() { cylinder(d=HUB_D + 10, h=20); for(a = [0 : 60 : 359]) { rotate([0, 0, a]) { translate([HUB_D/2, -5, 0]) cube([REVOLVER_PCD/2 - HUB_D/2, 10, 20]); translate([REVOLVER_PCD/2, 0, 0]) cylinder(d=ACRYL_OD + (HUB_WALL * 2), h=20); } } } translate([-(PF+GLOBAL_TOLERANCE)/2, -(PF+GLOBAL_TOLERANCE)/2, -1]) cube([PF + GLOBAL_TOLERANCE, PF + GLOBAL_TOLERANCE, 25]); rotate([0, 90, 45]) translate([-10, 0, 0]) cylinder(d=4.2, h=HUB_D); translate([0, 0, 20 - 4]) cylinder(d=SERVO_HORN_D + 0.3, h=4.2); for(a=[0:90:270]) { rotate([0, 0, a]) translate([HORN_PCD/2, 0, -1]) cylinder(d=2.5, h=22); } for(a = [0 : 60 : 359]) { rotate([0, 0, a]) translate([REVOLVER_PCD/2, 0, -1]) cylinder(d=ACRYL_OD + GLOBAL_TOLERANCE, h=22); } } for(a = [0 : 60 : 359]) { rotate([0, 0, a]) translate([REVOLVER_PCD/2, 0, LOWER_HUB_H - POCKET_DEPTH]) { color([0.1, 0.7, 0.9, 0.25]) difference() { cylinder(d=ACRYL_OD, h=150); translate([0, 0, -1]) cylinder(d=ACRYL_ID, h=152); } } } for(i = [0 : 5]) { rotate([0, 0, i * 60]) translate([REVOLVER_PCD/2, 0, 0]) { for(z_idx = [depleted[i] : 14]) { translate([0, 0, z_idx * 10 + drops[i]]) color(RING_CLRS[i], 0.8) { difference() { cylinder(d=ACRYL_ID - 0.2, h=10); translate([0, 0, -0.1]) cylinder(d=RING_IDS[i], h=10.2); } } } } } }
module h_bridge_adapter_plate() { difference() { hull() { translate([0, -Y_OFFSET, 0]) cylinder(d = X_BLOCK_L + 10, h = BRKT_H); translate([0, 0, 0]) cylinder(d = BRKT_D, h = BRKT_H); translate([0, Y_OFFSET, 0]) cylinder(d = X_BLOCK_L + 10, h = BRKT_H); } translate([0, -Y_OFFSET, 0]) { for(x = [-X_PITCH_X/2, X_PITCH_X/2]) { for(y = [-X_PITCH_Y/2, X_PITCH_Y/2]) { translate([x, y, -1]) cylinder(d = 4.5, h = BRKT_H + 2); } } } translate([0, Y_OFFSET, 0]) { for(x = [-X_PITCH_X/2, X_PITCH_X/2]) { for(y = [-X_PITCH_Y/2, X_PITCH_Y/2]) { translate([x, y, -1]) cylinder(d = 4.5, h = BRKT_H + 2); } } } translate([0, 0, -1]) cylinder(d = BRKT_ID, h = BRKT_H + 2); for(a = [45, 135, 225, 315]) { rotate([0, 0, a]) translate([Z_MOUNT_PCD/2, 0, -1]) cylinder(d = 4.5, h = BRKT_H + 2); } translate([-DRAIN_RADIUS, 0, -1]) cylinder(d = 14, h = BRKT_H + 2); } }
module z_cylinder_and_cage() { color([0.2, 0.5, 0.8, 0.25]) { difference() { translate([0, 0, -CUP_H]) cylinder(d=CUP_OD, h=CUP_H); translate([0, 0, -CUP_H - 0.1]) cylinder(d=CUP_ID, h=CUP_H + 0.2); } } color([0.85, 0.85, 0.85, 1.0]) { union() { difference() { translate([0, 0, -CUP_H - CAGE_H]) cylinder(d=CUP_OD, h=CAGE_H); translate([0, 0, -CUP_H - CAGE_H + FLOOR_H]) cylinder(d=CUP_ID, h=CAGE_H - FLOOR_H + 0.1); translate([-32.5, -CUP_OD/2 - 10, -CUP_H - CAGE_H + FLOOR_H + 5]) cube([65, CUP_OD + 20, CAGE_H - FLOOR_H - 10]); translate([0, 0, -CUP_H - CAGE_H - 0.1]) cylinder(d = MOTOR_BOSS_D + GLOBAL_TOLERANCE, h = FLOOR_H + 0.2); translate([0, 0, -CUP_H - CAGE_H - 1]) { for(x = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) { for(y = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) { translate([x, y, 0]) cylinder(d = MOTOR_HOLE_D, h = FLOOR_H + 3); } } } translate([0, 0, -CUP_H - CAGE_H - 1]) { for(a = [45, 135, 225, 315]) { rotate([0, 0, a]) translate([Z_MOUNT_PCD/2, 0, 0]) cylinder(d = 4.5, h = FLOOR_H + 2); } } translate([0, 0, -CUP_H - CAGE_H + FLOOR_H + LEAK_DRAIN_D/2]) rotate([0, -90, 0]) cylinder(d = LEAK_DRAIN_D, h = CUP_OD/2 + 10); translate([-DRAIN_RADIUS, 0, -CUP_H - CAGE_H - 1]) cylinder(d = GUIDE_PIPE_D + 1.0, h = FLOOR_H + 2); translate([-DRAIN_RADIUS, 0, -CUP_H - CAGE_H + FLOOR_H - BUSHING_H]) cylinder(d = BUSHING_OD + GLOBAL_TOLERANCE, h = BUSHING_H + 0.1); } difference() { translate([0, 0, -CUP_H - CAGE_H + FLOOR_H]) cylinder(d=LIP_D, h=LIP_H); translate([0, 0, -CUP_H - CAGE_H + FLOOR_H - 0.1]) cylinder(d = MOTOR_BOSS_D + GLOBAL_TOLERANCE, h = LIP_H + 0.2); } } } }
module z_moving_parts_assembly() { color([1.0, 0.5, 0.0, 1.0]) difference() { translate([0, 0, -PISTON_H]) cylinder(d=CUP_ID-0.5, h=PISTON_H); translate([0, 0, -PISTON_H - 1]) cylinder(d = SCREW_D + 0.5, h = PISTON_H + 2); translate([0, 0, -8]) cylinder(d = 15.0, h = 9, $fn = 6); translate([-DRAIN_RADIUS, 0, -PISTON_H - 1]) cylinder(d=DRAIN_D + GLOBAL_TOLERANCE, h=PISTON_H+2); } translate([0, 0, 0]) rotate([180, 0, 0]) color([0.9, 0.9, 0.2]) cylinder(d=8, h=290); translate([-DRAIN_RADIUS, 0, 0]) rotate([180, 0, 0]) color([0.55, 0.57, 0.6, 1.0]) difference() { cylinder(d=GUIDE_PIPE_D, h=260); translate([0,0,-1]) cylinder(d=GUIDE_PIPE_D - 2.0, h=262); } }
module z_motor_dummy() { difference() { union() { translate([-MOTOR_W/2, -MOTOR_W/2, -40]) cube([MOTOR_W, MOTOR_W, 40]); cylinder(d=MOTOR_BOSS_D, h=MOTOR_BOSS_H); } translate([0, 0, -45]) cylinder(d = SCREW_D + 2, h = 50); } }
module bushing_dummy() { color([0.8, 0.55, 0.3, 1.0]) difference() { cylinder(d = BUSHING_OD, h = BUSHING_H); translate([0, 0, -1]) cylinder(d = GUIDE_PIPE_D, h = BUSHING_H + 2); } }
module x_slider_block_dummy() { translate([-X_BLOCK_L/2, -X_BLOCK_W/2, 0]) cube([X_BLOCK_L, X_BLOCK_W, 10]); }
module water_reservoir_tank() { TANK_X = 180; TANK_Y = 330; TANK_H = 80; color([0.1, 0.5, 0.8, 0.4]) { difference() { cube([TANK_X, TANK_Y, TANK_H]); translate([4, 4, 4]) cube([TANK_X - 8, TANK_Y - 8, TANK_H]); } } color([0.2, 0.6, 1.0, 0.3]) translate([4, 4, 4]) cube([TANK_X - 8, TANK_Y - 8, 55]); }
module teflon_washer_dummy() { color([0.9, 0.9, 0.9]) translate([0, 0, 0]) difference() { cylinder(d=CARTRIDGE_OD, h=WASHER_T); translate([0, 0, -0.5]) cylinder(d=SHAFT_D + 0.5, h=WASHER_T + 1); } }