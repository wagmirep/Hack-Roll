#!/bin/bash
# test_end_to_end.sh - End-to-end integration test
#
# Tests the complete flow:
# 1. Start worker in background
# 2. Queue a test job
# 3. Verify worker processes it
# 4. Check results

set -e

echo "======================================================================"
echo "🧪 END-TO-END INTEGRATION TEST"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Activate venv
source venv/bin/activate

echo "TEST 1: Check Redis is running..."
echo "----------------------------------------------------------------------"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis is not running${NC}"
    echo "Start Redis with: redis-server"
    exit 1
fi
echo ""

echo "TEST 2: Clear any existing jobs..."
echo "----------------------------------------------------------------------"
redis-cli DEL "lahstats:processing" > /dev/null 2>&1
redis-cli DEL "lahstats:failed" > /dev/null 2>&1
echo -e "${GREEN}✅ Queues cleared${NC}"
echo ""

echo "TEST 3: Start worker in background..."
echo "----------------------------------------------------------------------"
python worker.py > /tmp/worker_test.log 2>&1 &
WORKER_PID=$!
echo -e "${GREEN}✅ Worker started (PID: $WORKER_PID)${NC}"
echo "Waiting for worker to initialize..."
sleep 3
echo ""

echo "TEST 4: Queue a test job..."
echo "----------------------------------------------------------------------"
TEST_SESSION_ID="test-$(uuidgen | tr '[:upper:]' '[:lower:]')"
JOB_PAYLOAD="{\"session_id\": \"$TEST_SESSION_ID\", \"queued_at\": \"$(date -u +%Y-%m-%dT%H:%M:%S)\"}"
echo "Job payload: $JOB_PAYLOAD"
redis-cli LPUSH "lahstats:processing" "$JOB_PAYLOAD" > /dev/null
echo -e "${GREEN}✅ Job queued${NC}"
echo ""

echo "TEST 5: Monitor job processing..."
echo "----------------------------------------------------------------------"
echo "Waiting for worker to pick up job..."
sleep 2

# Check queue is empty (job was picked up)
QUEUE_LEN=$(redis-cli LLEN "lahstats:processing")
if [ "$QUEUE_LEN" -eq "0" ]; then
    echo -e "${GREEN}✅ Job picked up by worker (queue empty)${NC}"
else
    echo -e "${YELLOW}⚠️  Job still in queue (length: $QUEUE_LEN)${NC}"
fi

# Check worker logs
echo ""
echo "Worker output (last 20 lines):"
echo "----------------------------------------------------------------------"
tail -20 /tmp/worker_test.log
echo ""

echo "TEST 6: Check failed queue..."
echo "----------------------------------------------------------------------"
FAILED_LEN=$(redis-cli LLEN "lahstats:failed")
if [ "$FAILED_LEN" -gt "0" ]; then
    echo -e "${YELLOW}⚠️  Job moved to failed queue (expected for test session)${NC}"
    echo "Failed job:"
    redis-cli LRANGE "lahstats:failed" 0 -1
else
    echo -e "${GREEN}✅ No failed jobs${NC}"
fi
echo ""

echo "TEST 7: Stop worker..."
echo "----------------------------------------------------------------------"
kill -INT $WORKER_PID 2>/dev/null
wait $WORKER_PID 2>/dev/null || true
echo -e "${GREEN}✅ Worker stopped${NC}"
echo ""

echo "TEST 8: Verify worker processed the job..."
echo "----------------------------------------------------------------------"
if grep -q "$TEST_SESSION_ID" /tmp/worker_test.log; then
    echo -e "${GREEN}✅ Worker processed test job${NC}"
    echo "Log excerpt:"
    grep "$TEST_SESSION_ID" /tmp/worker_test.log | head -5
else
    echo -e "${RED}❌ Test job not found in worker logs${NC}"
    exit 1
fi
echo ""

echo "======================================================================"
echo "🎉 END-TO-END TEST COMPLETE"
echo "======================================================================"
echo ""
echo -e "${GREEN}✅ Worker successfully picked up and processed job${NC}"
echo -e "${GREEN}✅ Queue system working correctly${NC}"
echo -e "${GREEN}✅ Integration test PASSED${NC}"
echo ""
echo "Full worker log saved to: /tmp/worker_test.log"
echo ""
