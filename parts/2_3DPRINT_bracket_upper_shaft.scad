// =========================================================================
// [부품] 상부 축 브래킷 (Upper Shaft Support Bracket)
// 가공: 3D 프린팅 (PLA)
// 원점: 보 상면 = Z=0, 축 중심 = XY 원점
// =========================================================================
include <_params.scad>

BRKT_T = 8.0;
BOTTOM_T = 10.0;
FLOAT_H = BOSS_H + WASHER_T - 10;  // 리볼버 Z 오프셋 (2mm)
UPPER_GAP = 2.0;           // 상단 허브 상면↔바닥판 하면 간격
DROP_H = (Z_TOP - PF) - (FLOAT_H + UPPER_HUB_Z + HUB_H + UPPER_GAP + BOTTOM_T);
BOSS_CLEAR = BOSS_OD + 1.0;
PLATE_W = 50.0;
HALF_BEAM = PF / 2;
HALF_GAP = BOSS_CLEAR/2 + 5;

difference() {
    union() {
        // ㅛ 상부: 좌측 탭
        translate([-PLATE_W/2, -HALF_BEAM - BRKT_T, 0])
            cube([PLATE_W, BRKT_T, PF]);
        // ㅛ 상부: 우측 탭
        translate([-PLATE_W/2, HALF_BEAM, 0])
            cube([PLATE_W, BRKT_T, PF]);
        // ㅛ 연결: 좌측 수평 연결판
        translate([-PLATE_W/2, -HALF_GAP - BRKT_T, -BRKT_T])
            cube([PLATE_W, HALF_GAP + BRKT_T - HALF_BEAM, BRKT_T]);
        // ㅛ 연결: 우측 수평 연결판
        translate([-PLATE_W/2, HALF_BEAM, -BRKT_T])
            cube([PLATE_W, HALF_GAP + BRKT_T - HALF_BEAM, BRKT_T]);
        // ㅛ 하부: 좌측 벽
        translate([-PLATE_W/2, -HALF_GAP - BRKT_T, -DROP_H])
            cube([PLATE_W, BRKT_T, DROP_H - BRKT_T]);
        // ㅛ 하부: 우측 벽
        translate([-PLATE_W/2, HALF_GAP, -DROP_H])
            cube([PLATE_W, BRKT_T, DROP_H - BRKT_T]);
        // ㅛ 하부: 바닥판
        translate([-PLATE_W/2, -HALF_GAP - BRKT_T, -DROP_H - BOTTOM_T])
            cube([PLATE_W, (HALF_GAP + BRKT_T) * 2, BOTTOM_T]);
    }
    // 보스 관통홀
    translate([0, 0, -DROP_H - BOTTOM_T - 1]) cylinder(d=BOSS_CLEAR, h=BOTTOM_T + 2);
    // 좌측 보 체결 볼트
    for(dx = [-15, 15])
        translate([dx, -HALF_BEAM - BRKT_T - 1, PF/2])
            rotate([-90, 0, 0]) cylinder(d=4.5, h=BRKT_T + 2);
    // 우측 보 체결 볼트
    for(dx = [-15, 15])
        translate([dx, HALF_BEAM - 1, PF/2])
            rotate([-90, 0, 0]) cylinder(d=4.5, h=BRKT_T + 2);
}
