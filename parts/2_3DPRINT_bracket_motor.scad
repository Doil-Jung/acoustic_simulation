// =========================================================================
// [부품] 모터 브래킷 (Motor Bracket)
// 가공: 3D 프린팅 (PLA) 또는 알루미늄 가공
// 원점: 브래킷 하면(상판 접촉면) = Z=0, 모터 축 = XY 원점
// =========================================================================
include <_params.scad>

BRKT_EXT = 30;
BRKT_TOTAL_X = BRKT_MOTOR_W + BRKT_EXT;

difference() {
    // 블록 본체 (모터영역 + 연장부)
    translate([-BRKT_MOTOR_W/2, -BRKT_MOTOR_W/2, 0])
        cube([BRKT_TOTAL_X, BRKT_MOTOR_W, BRKT_MOTOR_H]);
    // NEMA 17 마운트홀 (31mm 피치) + 하면 카운터보어 (단볼트용 깊은 심증)
    for(dx = [-MOTOR_PITCH/2, MOTOR_PITCH/2])
        for(dy = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) {
            translate([dx, dy, -1]) cylinder(d=MOTOR_HOLE_D, h=BRKT_MOTOR_H+2);
            translate([dx, dy, -1]) cylinder(d=MOTOR_CB_D, h=MOTOR_CB_DEPTH+1);  // 카운터보어 (깊이 19 → M3×10 단볼트)
        }
    // 중앙 관통홀 (모터 보스 클리어런스)
    translate([0, 0, -1]) cylinder(d=MOTOR_BOSS_D + 1, h=BRKT_MOTOR_H+2);
    // 상판 체결 슬롯 (연장부, X방향) — 베이스 플레이트 홀과 Y피치 25 공유
    for(dy = [-MOTOR_BOLT_PITCH/2, MOTOR_BOLT_PITCH/2])
        hull() {
            translate([BRKT_MOTOR_W/2 + 8, dy, -1]) cylinder(d=4.5, h=BRKT_MOTOR_H+2);
            translate([BRKT_MOTOR_W/2 + 8 + SLOT_LEN, dy, -1]) cylinder(d=4.5, h=BRKT_MOTOR_H+2);
        }
}
