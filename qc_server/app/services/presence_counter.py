class PresenceCounter:
    def __init__(self, session, min_area_frac=0.02, present_frames=3, absent_frames=5):
        self.session = session
        self.min_area_frac = min_area_frac
        self.present_frames = present_frames
        self.absent_frames = absent_frames
        self._count = 0
        self._present_streak = 0
        self._absent_streak = 0
        self._armed = False
        self._best = None
        self._best_conf = -1.0

    def _qualifies(self, det, frame_area):
        area = max(0, det.x2 - det.x1) * max(0, det.y2 - det.y1)
        return area >= self.min_area_frac * frame_area

    def _reset_candidate(self):
        self._present_streak = 0
        self._best = None
        self._best_conf = -1.0

    def update(self, frame, detections, scale=1.0):
        h, w = frame.shape[:2]
        frame_area = h * w
        qualifying = [d for d in detections if self._qualifies(d, frame_area)]

        if qualifying:
            self._absent_streak = 0
            if not self._armed:
                self._present_streak += 1
                best = max(qualifying, key=lambda d: d.confidence)
                if best.confidence > self._best_conf:
                    self._best = (frame.copy(), best, scale)
                    self._best_conf = best.confidence
                if self._present_streak >= self.present_frames:
                    bframe, bdet, bscale = self._best
                    self.session.add_captured(bframe, [bdet], bscale)
                    self._count += 1
                    self._armed = True
                    self._reset_candidate()
        else:
            self._absent_streak += 1
            if self._absent_streak >= self.absent_frames:
                self._armed = False
                self._reset_candidate()
            elif not self._armed:
                self._present_streak = 0
        return self._count
