// =========================================================================
// [부품] 컵 피스톤 (Cup Piston)
// 가공: 3D 프린팅 (PLA) × 1개
// 원점: 피스톤 상면(수면 접촉면) = Z=0, 중심 = XY 원점
// 포함: U패킹 홈 (1줄), 3D 프린팅용 일체형 T8 암나사 (접착 고정용)
// =========================================================================
include <_params.scad>

// U패킹 파라미터 (ø99.5 보어 대응)
UPAK_W = 6.0;      // U패킹 폭 (단면 폭)
UPAK_DEPTH = 5.0;   // 홈 깊이 (립이 바깥으로 돌출)
UPAK_Z = 10.0;      // 홈 중심 위치 (피스톤 상면에서)

// T8 4-start 리드스크류 암나사 생성 모듈 (공차 포함, 접착제 고정용)
// 규격: 외경 8.0mm, 리드 8.0mm (4줄 나사산)
module t8_internal_thread_subtraction(h) {
    // FDM 3D 프린팅 공차 및 접착제 충진 두께를 확보하기 위해 외경 8.4mm, 내경 6.6mm로 설계
    linear_extrude(height = h, twist = 360 * h / 8, slices = max(20, h * 5), convexity = 10) {
        difference() {
            circle(d = 8.4, $fn = 40);
            for (a = [0, 90, 180, 270]) {
                rotate([0, 0, a]) {
                    // 내향 삼각형 돌기 (나사 골 형성)
                    polygon(points = [[4.2, -0.8], [4.2, 0.8], [3.3, 0]]);
                }
            }
        }
    }
}

difference() {
    union() {
        // 피스톤 본체 (아크릴 원통 오차를 고려하여 외경 98.5mm로 유격 확보)
        translate([0, 0, -PISTON_H]) cylinder(d=CUP_ID-1.5, h=PISTON_H);
        // 배수구 하부 가이드 보스 (Boss)
        translate([-DRAIN_RADIUS, 0, -PISTON_H - 10])
            cylinder(d=15, h=10);
    }
    // 3D 프린팅 일체형 T8 나사산 (상면 Z=0 에서 5mm 남기고 진입)
    translate([0, 0, -PISTON_H - 0.1])
        t8_internal_thread_subtraction(PISTON_H - 5 + 0.1);
        
    // 배수관 단턱 소켓 (Z=-5 ~ 0 은 ø6.0 관통, Z=-30 ~ -5 은 ø8.2 소켓)
    translate([-DRAIN_RADIUS, 0, -5])
        cylinder(d=6.0, h=6.1);
    translate([-DRAIN_RADIUS, 0, -PISTON_H - 10 - 1])
        cylinder(d=DRAIN_D + GLOBAL_TOLERANCE, h=PISTON_H + 10 - 5 + 1.1);
        
    // U패킹 홈 (외주면, 1줄 - 넓은 직사각 단면)
    // U자 립이 상방(수압 방향)을 향하도록 장착 (실제 아크릴 내경 99.5mm 반영하여 홈 바닥 지름을 ø89.5로 변경)
    translate([0, 0, -UPAK_Z - UPAK_W/2]) difference() {
        cylinder(d=CUP_ID + 1, h=UPAK_W);
        translate([0, 0, -0.5]) cylinder(d=89.5, h=UPAK_W + 1);
    }
    
    // ── 피스톤 상면 배수 유로 홈 (Water Channel) ──
    // 음향 공명에 방해를 주지 않도록 중앙에서 7mm 떨어진 위치부터 배수구(X=-35) 방향으로 향하는 1줄의 홈만 형성 (폭 4mm, 깊이 3mm)
    rotate([0, 0, 180]) translate([7, -2, -3]) cube([DRAIN_RADIUS - 7 + 2, 4, 3.1]);
}
