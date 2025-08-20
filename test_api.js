// API连接测试脚本
async function testAPI() {
    console.log('🧪 开始测试API连接...');
    
    try {
        const response = await fetch('http://localhost:5001/explore', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                input: "请帮我分析哪只股票次日涨幅可能超过5%，并找出背后的模式和指标组合"
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('✅ API连接成功！');
            console.log('📊 返回数据结构:', Object.keys(result));
            console.log('🔍 复合指标探索:', result['复合指标探索']);
            console.log('📈 推荐指标数量:', result['推荐指标'] ? result['推荐指标'].length : 0);
            console.log('📊 可视化数据条数:', result['k线可视化数据'] ? result['k线可视化数据'].length : 0);
            return true;
        } else {
            console.log('❌ API请求失败:', response.status, response.statusText);
            return false;
        }
    } catch (error) {
        console.log('❌ API连接失败:', error.message);
        return false;
    }
}

// 在浏览器控制台中运行
if (typeof window !== 'undefined') {
    window.testAPI = testAPI;
    console.log('💡 在浏览器控制台中运行 testAPI() 来测试API连接');
}

// 在Node.js环境中运行
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { testAPI };
}
