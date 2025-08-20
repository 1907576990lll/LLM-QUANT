import random
from copy import deepcopy

class Node:
    def __init__(self, type, left=None, right=None, value=None):
        self.type = type  # 'leaf' or 'op'
        self.left = left
        self.right = left
        self.right = right
        self.value = value  # vector name if leaf, 'AND'/'OR' if op

    def __deepcopy__(self, memo):
        if self.type == "leaf":
            return Node("leaf", value=self.value)
        else:
            return Node("op", left=deepcopy(self.left, memo), right=deepcopy(self.right, memo), value=self.value)

    def to_string(self):
        if self.type == "leaf":
            return self.value
        else:
            return f"({self.left.to_string()} {self.value} {self.right.to_string()})"

    def evaluate(self, vectors):
        if self.type == "leaf":
            return vectors[self.value]
        else:
            left_vec = self.left.evaluate(vectors)
            right_vec = self.right.evaluate(vectors)
            if self.value == "AND":
                return [x & y for x, y in zip(left_vec, right_vec)]
            elif self.value == "OR":
                return [x | y for x, y in zip(left_vec, right_vec)]

    def get_used_names(self):
        """获取此节点（子树）中使用的所有向量名"""
        if self.type == "leaf":
            return {self.value}
        else:
            return self.left.get_used_names().union(self.right.get_used_names())


class StrategyExplore:
    def __init__(self, vectors, seed, max_depth=2, generations=100, pop_size=50, crossover_rate=0.9, mutation_rate=0.2, max_elements=None):
        self.vectors = vectors
        self.seed = seed
        self.vector_names = list(vectors.keys())
        self.MAX_DEPTH = max_depth
        self.GENERATIONS = generations
        self.POP_SIZE = pop_size
        self.CROSSOVER_RATE = crossover_rate
        self.MUTATION_RATE = mutation_rate
        # 如果未指定 max_elements，则默认为所有向量名的数量
        self.max_elements = max_elements if max_elements is not None else len(self.vector_names)

    def generate_random_tree(self, depth=0, available_names=None):
        """
        生成随机树，确保每个向量名只使用一次。
        :param depth: 当前深度
        :param available_names: 当前可用的向量名集合
        :return: 生成的Node
        """
        if available_names is None:
            available_names = set(self.vector_names)

        # 终止条件：达到最大深度 或 可用向量名为空 或 已使用向量名数量达到 max_elements
        if depth >= self.MAX_DEPTH or len(available_names) == 0:
            # 尝试从可用名中选一个作为叶子
            if available_names:
                name = random.choice(list(available_names))
                return Node("leaf", value=name)
            else:
                # 如果没有可用名，返回None（这种情况在调用时需要处理）
                return None

        # 如果深度不够且还有可用名，则继续构建
        # 以一定概率直接生成叶子节点（尤其在深度接近MAX_DEPTH时）
        if depth == self.MAX_DEPTH - 1 or random.random() < 0.5 * (1 - depth / self.MAX_DEPTH):
            name = random.choice(list(available_names))
            return Node("leaf", value=name)

        # 尝试生成操作节点
        op = random.choice(["AND", "OR"])

        # 随机划分可用名给左右子树，确保至少一边有可用名
        names_list = list(available_names)
        random.shuffle(names_list)
        # 确保至少给一边分配一个名字
        split_point = random.randint(1, len(names_list) - 1) if len(names_list) > 1 else 1
        left_names = set(names_list[:split_point])
        right_names = set(names_list[split_point:])

        # 递归生成左右子树
        left_child = self.generate_random_tree(depth + 1, left_names)
        right_child = self.generate_random_tree(depth + 1, right_names)

        # 如果任一子树生成失败（返回None），则退化为生成一个叶子节点
        if left_child is None or right_child is None:
            if left_child:
                return left_child
            elif right_child:
                return right_child
            else:
                # 极端情况，都失败了，尝试从原始可用名中选一个
                if available_names:
                    name = random.choice(list(available_names))
                    return Node("leaf", value=name)
                else:
                    return None

        return Node("op", left=left_child, right=right_child, value=op)

    def evaluate_fitness(self, tree):
        if tree is None:
            # 处理无效树的情况，返回一个很差的适应度
            return float('inf'), [0] * len(self.seed)
        result_vector = tree.evaluate(self.vectors)
        hamming_distance = sum(x != y for x, y in zip(result_vector, self.seed))
        return hamming_distance, result_vector

    def tournament_selection(self, population, k=3):
        contestants = random.sample(population, k)
        contestant_scores = [(ind, self.evaluate_fitness(ind)[0]) for ind in contestants]
        best = min(contestant_scores, key=lambda x: x[1])
        return best[0]

    def crossover(self, parent1, parent2):
        if random.random() < self.CROSSOVER_RATE and parent1 is not None and parent2 is not None:
            # 获取两个父代使用的向量名集合
            used_names1 = parent1.get_used_names()
            used_names2 = parent2.get_used_names()

            # 找到parent1中可用于替换的子树（不能是根节点，且其使用的名在parent2中不存在）
            # 为了简化，我们选择parent1的左子树或右子树作为交叉点（如果存在且其使用的名与parent2无交集）
            # 这是一个简化的交叉策略，更复杂的策略可以随机选择子树
            if parent1.type == "op":
                # 检查左子树
                if parent1.left.type == "op" and parent1.left.get_used_names().isdisjoint(used_names2):
                    # 左子树可替换，用parent2替换它
                    new_left = deepcopy(parent2)
                    return Node(parent1.type, left=new_left, right=deepcopy(parent1.right), value=parent1.value)
                # 检查右子树
                elif parent1.right.type == "op" and parent1.right.get_used_names().isdisjoint(used_names2):
                    # 右子树可替换，用parent2替换它
                    new_right = deepcopy(parent2)
                    return Node(parent1.type, left=deepcopy(parent1.left), right=new_right, value=parent1.value)
                # 如果左右子树都不能直接替换（因为名字冲突），则尝试用parent2的某个子树替换parent1的某个子树
                # 这里简化处理：如果直接替换不行，就返回parent1的深拷贝
            # 如果parent1是叶子节点，或者无法进行有效交叉，则返回parent1的深拷贝
        return deepcopy(parent1)

    def mutate(self, tree):
        if random.random() < self.MUTATION_RATE and tree is not None:
            # 获取当前树使用的向量名
            used_names = tree.get_used_names()
            # 计算剩余可用的向量名
            available_names = set(self.vector_names) - used_names
            if len(available_names) > 0 and len(used_names) < self.max_elements:
                # 有可用名且未达到最大元素数量限制，可以进行变异
                # 简单变异：用一个新生成的、使用可用名的随机子树替换当前树
                new_subtree = self.generate_random_tree(available_names=available_names)
                if new_subtree is not None:
                    return new_subtree
        return tree # 如果变异失败或不进行变异，则返回原树

    def evolve(self):
        # 初始化种群
        population = []
        for _ in range(self.POP_SIZE):
            tree = self.generate_random_tree()
            population.append(tree)

        best_tree = None
        best_fitness = float('inf')

        for gen in range(self.GENERATIONS):
            new_population = []
            for i in range(self.POP_SIZE):
                parent1 = self.tournament_selection(population)
                parent2 = self.tournament_selection(population)
                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                new_population.append(child)

            population = new_population

            # 找出当前代中最佳个体
            scores = [(ind, self.evaluate_fitness(ind)[0]) for ind in population if ind is not None]
            if scores:  # 确保有有效个体
                current_best = min(scores, key=lambda x: x[1])
                current_tree, current_fit = current_best

                if current_fit < best_fitness:
                    best_fitness = current_fit
                    best_tree = current_tree

            # 打印当前最佳（如果存在）
            if best_tree is not None:
                print(f"Generation {gen}, Best Fitness: {best_fitness}, Expression: {best_tree.to_string()}")
            else:
                print(f"Generation {gen}, Best Fitness: {best_fitness}, Expression: None")

        # 处理最终结果
        if best_tree is not None:
            final_vector = best_tree.evaluate(self.vectors)
            return best_tree.to_string(), final_vector, best_fitness
        else:
            # 如果没有找到有效解，返回一个默认值
            default_vector = [0] * len(self.seed)
            return "No valid expression found", default_vector, float('inf')


# 使用示例
if __name__ == "__main__":
    vectors = {
        "周流量5日累加趋势": [1, 1, 1, 1, 0, 1, 1, 0, 0, 1],
        "TD序列低位9号反转信号": [1, 1, 1, 0, 1, 0, 0, 0, 0, 1],
        "DDX正向放大": [1, 1, 0, 0, 0, 0, 0, 1, 1, 1],
        "动能指标G3/G5异动释放买点信号": [0, 1, 1, 1, 0, 1, 1, 1, 0, 1],
        "VWAP上穿移动平均线": [1, 0, 1, 1, 1, 0, 1, 1, 0, 0],
        "25周期双重EMA支撑压力线": [0, 1, 0, 1, 1, 1, 0, 0, 1, 1],
        "6日与11日均价差变化率": [1, 1, 1, 0, 0, 1, 1, 0, 1, 1],
        "回调形态中的凹口突破": [1, 0, 1, 1, 0, 1, 0, 1, 1, 0],
        "J值高位死叉逃顶信号": [0, 0, 1, 1, 1, 1, 0, 1, 0, 1],
        "能量指标危险区（18）": [1, 1, 0, 0, 1, 0, 1, 0, 1, 0],
        "diff与dea同步上扬": [1, 0, 1, 1, 0, 1, 0, 0, 1, 1],
    }
    seed = [1, 1, 1, 0, 1, 1, 1, 0, 0, 1]

    # 设置 max_elements 来控制表达式中最多使用的不同向量数量
    se = StrategyExplore(vectors, seed, max_depth=3, generations=200, pop_size=50, max_elements=3)
    best_expr, result_vector, distance = se.evolve()
    print(f"\nBest Expression: {best_expr}")
    print(f"Result Vector: {result_vector}")
    print(f"Hamming Distance: {distance}")

    # 验证结果中是否有重复的向量名
    if best_expr != "No valid expression found":
        names_in_expr = set()
        # 这里简单地通过字符串分割来提取名字（实际应遍历树结构，但为演示目的）
        # 更准确的方式是遍历Node树的get_used_names()方法
        import re
        found_names = re.findall(r'\b(?:' + '|'.join(re.escape(name) for name in vectors.keys()) + r')\b', best_expr)
        print(f"Vector names found in expression: {found_names}")
        if len(found_names) != len(set(found_names)):
            print("ERROR: Duplicate vector names found in the expression!")
        else:
            print("SUCCESS: All vector names in the expression are unique.")
    else:
        print("No valid expression was generated.")