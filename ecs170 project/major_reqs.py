
#courses = ["MAT 067", "MAT 022A", "MAT 067", "BIS 002A", "BIS 002B", "BIS 002C", "CHE 002A"]

class CourseNode:
    val = None
    chooseVal = 0 #for "choose one/two/..." root nodes, this will be >0
    child_courses = [] #list of course nodes that fall under the "choose one" node

def checkMajorReqSubtree(parent_node, course_name):
    score = 0
    for node in parent_node.child_courses:
        if node.chooseVal != 0:
            score = checkMajorReqSubtree(node, course_name)
            if score==1 and node.chooseVal == 0:
                parent_node.chooseVal = parent_node.chooseVal - 1
            if score != 0:
                break
        else:
            if course_name == node.val:
                score = 1
                parent_node.chooseVal = parent_node.chooseVal - 1
                break
    return score

def checkOffMajorReqs(majorRequirements, courses):
    for course in courses:
        for node in majorRequirements:
            if node.chooseVal != 0:
                ret_val = checkMajorReqSubtree(node, course)
                if ret_val != 0:
                    break
            else:
                if (course == node.val):
                    break


def getCourseScore(majorRequirementsCopy, course):
    score = 0
    
    for node in majorRequirementsCopy:
        if node.chooseVal != 0:
            score = checkMajorReqSubtree(node, course)
            if score != 0:
                break
        else:
            if (course == node.val):
                score = 1
                break
            
    return score