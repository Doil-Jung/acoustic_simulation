// =========================================================================
// [구매] 벨트 구동 모터 + 풀리 세트
// 구매: NEMA17 + GT2 20T 풀리 + GT2 타이밍벨트
// 메인 파일 belt_drive_motor_assembly() 구매 부품만 추출 (브래킷 제외)
// 원점: 모터 하면(브래킷 접촉면) = Z=0, 축 상향
// =========================================================================
include <_params.scad>

MOT_BODY_L = 43;
SHAFT_L = 24;
PULLEY_Z = MOT_BODY_L + 5;

// ── ① NEMA 17 모터 본체 (축 상향) ──
color([0.1, 0.1, 0.1])
    translate([-MOTOR_W/2, -MOTOR_W/2, 0])
        cube([MOTOR_W, MOTOR_W, MOT_BODY_L]);

// ── ② 모터 보스 (ø22 × 2mm, 상면) ──
color([0.25, 0.25, 0.25])
    translate([0, 0, MOT_BODY_L])
        cylinder(d=MOTOR_BOSS_D, h=MOTOR_BOSS_H);

// ── ③ 모터 축 (상면에서 위로 돌출) ──
color([0.7, 0.7, 0.7])
    translate([0, 0, MOT_BODY_L])
        cylinder(d=5, h=SHAFT_L);

// ── ④ GT2 20치 풀리 ──
color([0.8, 0.75, 0.1]) translate([0, 0, PULLEY_Z]) difference() {
    union() {
        cylinder(d=SMALL_PULLEY_OD, h=GT2_BELT_W + 2);
        cylinder(d=SMALL_PULLEY_OD + 4, h=1);               // 하부 플랜지
        translate([0, 0, GT2_BELT_W + 1])
            cylinder(d=SMALL_PULLEY_OD + 4, h=1);           // 상부 플랜지
    }
    translate([0, 0, -1]) cylinder(d=5.2, h=GT2_BELT_W + 4);
}

// ── ⑤ 배선 커넥터 (모터 하면) ──
color([0.9, 0.9, 0.9])
    translate([-6, -5, -3])
        cube([12, 10, 3]);
