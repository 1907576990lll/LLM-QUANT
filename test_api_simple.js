// 简单的API测试脚本
async function testAPI() {
    console.log('🧪 测试API连接...');
    
    try {
        const response = await fetch('http://localhost:5001/explore', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                input: "买入次日涨幅超1%"
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('✅ API连接成功！');
            console.log('📊 返回数据:', Object.keys(result));
            return true;
        } else {
            console.log('❌ API请求失败:', response.status);
            return false;
        }
    } catch (error) {
        console.log('❌ API连接失败:', error.message);
        return false;
    }
}

// 运行测试
testAPI();
