// =========================================================================
// [도면] 아크릴 레이저 커팅용 2D 도면 추출기 (Laser Cutting 2D Drawings)
// 가공: 아크릴 5T 레이저 커팅 후 적층하여 3D 형상 제작
// 사용방법:
// 1. OpenSCAD에서 이 파일을 엽니다.
// 2. Customizer 창 또는 아래 'PART_SELECT' 변수값을 원하는 레이어로 변경합니다.
// 3. F6(렌더링)을 누릅니다.
// 4. File -> Export as DXF (또는 SVG)를 선택하여 캐드 도면으로 저장합니다.
// =========================================================================

include <parts/_params.scad>

// [레이저 커팅 대상 파트 선택]
// "base_plate_layer_1_2" : 상판 1층 및 2층 (Z = -10 ~ 0, ø36 베어링 단 가공부)
// "base_plate_layer_3"   : 상판 3층 (Z = -15 ~ -10, ø13 축 관통홀)
// "hub_lower_boss"       : 하단 허브 보스 (2장 적층, ø35)
// "hub_lower_disc_1_2"   : 하단 허브 디스크 1층 및 2층 (Z = 0 ~ 10, ø100.5 관통홀)
// "hub_lower_disc_3"     : 하단 허브 디스크 3층 (Z = 10 ~ 15, ø110.2 아크릴관 소켓)
// "hub_middle_disc_1_2"  : 중단 허브 디스크 1층 및 2층 (Z = 0 ~ 10, ø110.2 관통홀)
// "hub_middle_disc_3"    : 중단 허브 디스크 3층 (Z = 10 ~ 15, ø361.3 풀리 외주 림)
// "hub_upper_disc_1"     : 상단 허브 디스크 1층 (Z = 0 ~ 5, ø110.2 아크릴관 소켓)
// "hub_upper_disc_2_3"   : 상단 허브 디스크 2층 및 3층 (Z = 5 ~ 15, ø100.5 관통홀)
// "hub_upper_boss"       : 상단 허브 보스 (2장 적층, ø35)
PART_SELECT = "base_plate_layer_1_2"; // [base_plate_layer_1_2, base_plate_layer_3, hub_lower_boss, hub_lower_disc_1_2, hub_lower_disc_3, hub_middle_disc_1_2, hub_middle_disc_3, hub_upper_disc_1, hub_upper_disc_2_3, hub_upper_boss]

$fn = 100;
SQ = SHAFT_SQ + GLOBAL_TOLERANCE; // 20.2mm 사각 축 홀

// 실행부
if (PART_SELECT == "base_plate_layer_1_2") {
    base_plate_2d(layer_type = 1);
} else if (PART_SELECT == "base_plate_layer_3") {
    base_plate_2d(layer_type = 2);
} else if (PART_SELECT == "hub_lower_boss" || PART_SELECT == "hub_upper_boss") {
    hub_boss_2d();
} else if (PART_SELECT == "hub_lower_disc_1_2" || PART_SELECT == "hub_upper_disc_2_3") {
    hub_lower_disc_1_2_2d();
} else if (PART_SELECT == "hub_lower_disc_3" || PART_SELECT == "hub_middle_disc_1_2" || PART_SELECT == "hub_upper_disc_1") {
    hub_lower_disc_3_2d();
} else if (PART_SELECT == "hub_middle_disc_3") {
    hub_middle_disc_3_2d();
}

// ── [1] 상판 2D 단면 정의 ──
module base_plate_2d(layer_type) {
    // 플레이트 중심을 원점으로 맞추기 위한 이송 오프셋
    CX = (X_L + X_M + PF)/2; // -115
    CY = (Y_F + Y_B + PF)/2; // 0
    
    translate([-CX, -CY]) difference() {
        // 상판 외경 사각형
        translate([X_L, Y_F]) square([(X_M + PF) - X_L, (Y_B + PF) - Y_F]);
        
        // 3030 알루미늄 프로파일 프레임 기둥 통과 홈 (네 모서리 절단)
        translate([X_L - 0.1, Y_B - 0.1]) square([PF + 0.2, PF + 0.2]);
        translate([X_L - 0.1, Y_F - 0.1]) square([PF + 0.2, PF + 0.2]);
        translate([X_M, Y_B - 0.1]) square([PF + 0.2, PF + 0.2]);
        translate([X_M, Y_F - 0.1]) square([PF + 0.2, PF + 0.2]);
        
        // 아크릴 카트리지 진입용 장공 (DROP_X=+5 위치 정렬)
        translate([DROP_X, -(CUP_OD + 1)/2]) square([CARTRIDGE_OD, CUP_OD + 1]);
        translate([DROP_X, 0]) circle(d = CUP_OD + 1);
        
        // 회전축 베어링 수용부
        if (layer_type == 1) {
            // Z = -10 ~ 0 구간: ø36mm 베어링 단 가공 (Layer 1, 2)
            translate([REVOLVER_CX, 0]) circle(d = 36);
        } else {
            // Z = -15 ~ -10 구간: ø13mm 회전축 통과홀 (Layer 3)
            translate([REVOLVER_CX, 0]) circle(d = 13);
        }
        
        // NEMA17 벨트 모터 마운트 조절용 볼트 구멍 (M4 관통홀)
        for(hx = [MOTOR_BOLT_X_NOMINAL, MOTOR_BOLT_X_SHIFT])
            for(hy = [BELT_MOTOR_Y - MOTOR_BOLT_PITCH/2, BELT_MOTOR_Y + MOTOR_BOLT_PITCH/2])
                translate([hx, hy]) circle(d = 4.5);
    }
}

// ── [2] 보스 2D 단면 정의 ──
module hub_boss_2d() {
    difference() {
        circle(d = BOSS_OD); // ø35
        square([SQ, SQ], center = true); // 20.2mm 사각 회전축 홀
    }
}

// ── [3] 하단 허브 디스크 1, 2층 / 상단 허브 디스크 2, 3층 2D 단면 ──
module hub_lower_disc_1_2_2d() {
    difference() {
        circle(d = CARTRIDGE_OD); // ø358
        square([SQ, SQ], center = true);
        for(a = [0 : 60 : 359]) rotate([0, 0, a])
            translate([REVOLVER_PCD/2, 0]) circle(d = CUP_ID + 0.5); // ø100.5 관통홀
    }
}

// ── [4] 하단 허브 디스크 3층 / 중단 허브 디스크 1, 2층 / 상단 허브 디스크 1층 2D 단면 ──
module hub_lower_disc_3_2d() {
    difference() {
        circle(d = CARTRIDGE_OD); // ø358
        square([SQ, SQ], center = true);
        for(a = [0 : 60 : 359]) rotate([0, 0, a])
            translate([REVOLVER_PCD/2, 0]) circle(d = ACRYL_OD + GLOBAL_TOLERANCE); // ø110.2 아크릴관 결합 소켓
    }
}

// ── [5] 중단 허브 디스크 3층 (벨트 풀리용 가이드 림) 2D 단면 ──
module hub_middle_disc_3_2d() {
    difference() {
        circle(d = BIG_PULLEY_OD); // ø361.3 풀리용 가이드 디스크
        square([SQ, SQ], center = true);
        for(a = [0 : 60 : 359]) rotate([0, 0, a])
            translate([REVOLVER_PCD/2, 0]) circle(d = ACRYL_OD + GLOBAL_TOLERANCE); // ø110.2 관통홀
    }
}
