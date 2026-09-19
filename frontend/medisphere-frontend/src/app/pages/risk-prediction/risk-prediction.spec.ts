import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RiskPrediction } from './risk-prediction';

describe('RiskPrediction', () => {
  let component: RiskPrediction;
  let fixture: ComponentFixture<RiskPrediction>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RiskPrediction]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RiskPrediction);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
