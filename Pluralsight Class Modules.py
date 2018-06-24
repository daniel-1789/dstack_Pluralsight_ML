import numpy as np
import pandas as pd
import array
import sqlite3
import sys



def jaccard_distances_array(in_array, num_users):
    """
    Create an array of Jaccard distances for N users by N users - in the sample set this would
    be 10,000 by 10,000. In the end I did not use this method for my final design but am
    maintaining it for the time being.
    
    Inputs - 
    in_array - a 1D array w/ an entry per user. The entry is a set for Jaccard distance calcualtion.
    num_users - Number of users
    
    Returns - A Jaccard distance array
    """

    distance_sets = np.full((num_users, num_users),1.0)

    for src_index, src_row in enumerate(distance_sets):

        for dst_index, dst_row in enumerate(in_array):
            # do a triangle and mirror
            if src_index > dst_index:
                continue
            src_row = in_array[src_index]
            dst_row = in_array[dst_index]
            if src_row and dst_row:
                # if either set is empty no point continuing. Otherwise get cardinalities
                intersection_cardinality = len(set.intersection(*[set(src_row), set(dst_row)]))
                union_cardinality = len(set.union(*[set(src_row), set(dst_row)]))
                distance_sets[src_index][dst_index] = 1.0 - (
                    float(intersection_cardinality)/float(union_cardinality))
                
    for src_index, src_row in enumerate(distance_sets):
        for dst_index, dst_row in enumerate(distance_sets):
            # mirror half of the triangle
            if src_index > dst_index:
                distance_sets[src_index][dst_index] = distance_sets[dst_index][src_index]
        print(distance_sets[src_index])
    return distance_sets





def jaccard_distances_user(in_array, user_handle, num_users):
    """
    For a given user_handle, calculate the distance to all other users. 

    
    Inputs - 
    in_array - a 1D array w/ an entry per user. The entry is a set for Jaccard distance calcualtion.
    user_handle - 1-based user handle
    num_users - Number of users
    
    Returns - A Jaccard distance array for the given user handle   
    """
    
    distance_sets = np.full((num_users),1.0) # initialize all distances to 1
    src_index = user_handle - 1 # array is 0-based
    
    for dst_index, dst_row in enumerate(in_array):
        src_row = in_array[src_index]
        dst_row = in_array[dst_index]
        if src_row and dst_row:
            # if either set is empty no point continuing. Otherwise get cardinalities
            intersection_cardinality = len(set.intersection(*[set(src_row), set(dst_row)]))
            if (intersection_cardinality > 0):
                # if the intersection is 0 the distance will be the default max, 1
                union_cardinality = len(set.union(*[set(src_row), set(dst_row)]))
                distance_sets[dst_index] = 1.0 - (
                    float(intersection_cardinality)/float(union_cardinality))
    return distance_sets




def calculate_3_axis_distances_for_one_handle(user_handle):
    """
    For a given user_handle, calculate the distance to all other users across all three axes. 
    Assumes Assessments_Obj, Interests_Obj, and Classes_Obj are global. Performs multiple 
    Jaccard Distance caluclations and then uses the Pythagorean Theorem to combine them.
    
    In the end I did not use this method for my final design but am
    maintaining it for the time being.
    
    Inputs - 
    in_array - a 1D array w/ an entry per user. The entry is a set for Jaccard distance calcualtion.
    user_handle - 1-based user handle
    num_users - Number of users
    
    Returns - A Jaccard distance array for the given user handle   
    """
    # note user-handle is 1-based
    assessment_distance = Assessments_Obj.calculate_handle_jaccard_distances(user_handle)
    interests_distance = Interests_Obj.calculate_handle_jaccard_distances(user_handle)
    classes_distance = Classes_Obj.calculate_handle_jaccard_distances(user_handle)
    
    overall_distance = (np.sqrt((assessment_distance ** 2) + (interests_distance ** 2) +                                 (classes_distance ** 2))) / np.sqrt(3)
    
    return overall_distance




def sql_3_axis_distances_for_one_handle(Assmnts_Obj, Ints_Obj, Cls_Obj, user_handle):
    """
    For a given user_handle, calculate the distance to all other users across all three axes. 
    Assumes Assessments_Obj, Interests_Obj, and Classes_Obj are global. Performs multiple 
    Jaccard Distance caluclations and then uses the Pythagorean Theorem to combine them. 
    Write results to SQLite table.
    
    Inputs - 
    Assmnts_Obj - A member of the Assessments class
    Ints_Obj - A member of the Interests class
    Cls_Obj - A member of the Classes class
    user_handle - 1-based user handle
    
    Returns - Nothing. Results written to SQLite table.   
    """

    # note user-handle is 1-based
    assessment_distance = Assmnts_Obj.calculate_handle_jaccard_distances(user_handle)
    interests_distance = Ints_Obj.calculate_handle_jaccard_distances(user_handle)
    classes_distance = Cls_Obj.calculate_handle_jaccard_distances(user_handle)
    
    overall_distance = (np.sqrt((assessment_distance ** 2) + (interests_distance ** 2) +                                 (classes_distance ** 2))) / np.sqrt(3)
    conn = sqlite3.connect('dstack.db')
  
    c = conn.cursor()
    for idx, entry in enumerate(overall_distance):
        c.execute("""INSERT INTO distance_matrix VALUES (?, ?, ?)""", 
                  (user_handle, idx + 1, overall_distance[idx],))
        
        
        
    # Save (commit) the changes
    conn.commit()

    conn.close()

    return 




class PS_Data:
    """
    Parent class for Assessments, Intersts, and Classes. Stores dataframe for corresponding csv
    file as well as user_data_sets which stores sets that indicate Assessments, Intersts, and
    Classes for all users. 
    """
    def __init__(self, input_file):
        self.input_file = input_file
        self.data = None
        self.user_list = None
        self.num_users = 0
        self.user_data_sets = None
        self.jaccard_distances = None
        
    def load_data(self):
        """
        Read csv file into a pandas dataframe.
        """
        try:
            self.data = pd.read_csv(self.input_file)
        except FileNotFoundError:
            print('load_data - could not find file {0}'.format(self.input_file))
            sys.exit() # cease execution
                  

    def get_user_handles(self):
        """
        Get all the unique user handles associated with this dataframe
        """
        return self.data.user_handle.unique()
    
    def set_users(self, user_list):
        """
        Use the user_list to define all possible users, not just those associated 
        with the inheriting classes. Allows the set arrays to match in size between
        classes.
        """
        self.user_list = user_list
        try:
            self.num_users = len(user_list)
        except TypeError:
            print('set_users - user_list is empty')
            sys.exit()
        
    def calculate_all_jaccard_distances(self):
        self.jaccard_distances = jaccard_distances_array(self.user_data_sets, self.num_users)
        
    def calculate_handle_jaccard_distances(self, handle):
        return jaccard_distances_user(self.user_data_sets, handle, self.num_users)

        




class Assessments(PS_Data):
    """
    Class to store assessment related information.
    """
    def __init__(self, input_file):
        PS_Data.__init__(self, input_file)
        
        
        self.load_data()
    
        
    def load_user_data_set(self):
        """
        Convert the dataframe into a user handle based array of sets indicating
        assessment results.
        """

        try:
            assessment_set = [set() for x in range(len(self.user_list))]
        except TypeError:
            print('load_user_data_set - user_list is empty')
            sys.exit()
        
        # Tack on _Novice, _Proficient, and _Expert to the assessment names -
        # for an Expert use all three, Proficient uses two.
        for index, row in self.data.iterrows():
            curr_user = assessment_set[row.user_handle-1]
            if (row.user_assessment_score >= 200):
                curr_user.add(row.assessment_tag +'_Expert')
                curr_user.add(row.assessment_tag + '_Proficient')
                curr_user.add(row.assessment_tag +'_Novice')
            elif (row.user_assessment_score >= 100):
                curr_user.add(row.assessment_tag + '_Proficient')
                curr_user.add(row.assessment_tag + '_Novice')
            else:
                curr_user.add(row.assessment_tag + '_Novice')
        self.user_data_sets = assessment_set




class Interests(PS_Data):
    """
    Class to store interests related information.
    """

    def __init__(self, input_file):
        
        PS_Data.__init__(self, input_file)
        
        
        self.load_data()
    
    def load_user_data_set(self):
        """
        Convert the dataframe into a user handle based array of sets indicating
        interests.
        """

        try:
            interest_set = [set() for x in range(len(self.user_list))]
        except TypeError:
            print('load_user_data_set - user_list is empty')
            sys.exit()


        for index, row in self.data.iterrows():
            curr_user = interest_set[row.user_handle-1]
            curr_user.add(row.interest_tag)
        self.user_data_sets = interest_set




class Classes(PS_Data):
    """
    Class to store class-interest related information.
    """

    def __init__(self, input_file, tags_file):
        PS_Data.__init__(self, input_file)
        self.tags_file = tags_file
        self.load_data()
    
    def load_data(self):
        """
        Loading dataframe for Classes is slightly more complex as it also makes use of the 
        tags file.
        """
        try: 
            self.data_course_tags = pd.read_csv(self.tags_file)
        except FileNotFoundError:
            print('load_data - could not find tags file {0}'.format(self.tags_file))
            sys.exit() # cease execution

        try:    
            self.data  = pd.read_csv(self.input_file)
        except FileNotFoundError:
            print('load_data - could not find file {0}'.format(self.input_file))
            sys.exit() # cease execution

        # get the course_tag for each course
        self.data = self.data.merge(self.data_course_tags[['course_id', 'course_tags']], on=['course_id'])
        self.data.drop('view_date', axis=1, inplace=True)
        self.data.drop('author_handle', axis=1, inplace=True)
        self.data.drop('view_time_seconds', axis=1, inplace=True)
        self.data.drop('course_id', axis=1, inplace=True)
        self.data.drop_duplicates(inplace=True)
        
        
    def load_user_data_set(self):  
        """
        Convert the dataframe into a user handle based array of sets indicating
        class interests.
        """

        try:
            course_set = [set() for x in range(len(self.user_list))]
        except TypeError:
            print('load_user_data_set - user_list is empty')

        # Tack on _Beginner, _Intermediate, and _Advanced to the class names -
        # for an Expert use all three, Proficient uses two.

        for index, row in self.data.iterrows():
            curr_user = course_set[row.user_handle-1]
            course_tag = str(row.course_tags)
            course_tag = course_tag + '_' 
            curr_user.add(course_tag + row.level)
            if row.level == 'Advanced':
                curr_user.add(course_tag + 'Intermediate')
                curr_user.add(course_tag + 'Beginner')
            elif row.level == 'Intermediate':
                curr_user.add(course_tag + 'Beginner')
        self.user_data_sets = course_set





def create_sql_table():
    """
    Connect to the database 'dstack.db' and create the distance_matrix table.
    Delete the table if it already exists.
    
    """
    conn = sqlite3.connect('dstack.db')

    c = conn.cursor()

    # Create table

    c.execute('''DROP TABLE IF EXISTS distance_matrix''')

    c.execute('''CREATE TABLE distance_matrix
             (src_usr integer, dst_usr integer, distance real)''')
    # Save the changes
    conn.commit()

    conn.close()



"""
Main function.
"""

def main():
    Assessments_Obj = Assessments('data_files_ml_engineer/user_assessment_scores.csv')
    Interests_Obj = Interests('data_files_ml_engineer/user_interests.csv')
    Classes_Obj = Classes('data_files_ml_engineer/user_course_views.csv', 'data_files_ml_engineer/course_tags.csv')


    # make a list of the three objects
    Obj_List = [Assessments_Obj,Interests_Obj, Classes_Obj]


    # get all our users - as it turns out there are 10,000 ranging from 1 to 10,000.
    # This code will take advantage of that - in a more generic problem we would need
    # to accept the possibility of gaps.
    user_lists = [obj.get_user_handles() for obj in Obj_List]
    user_list = np.unique([item for sublist in user_lists for item in sublist])

    # tell each object about the users
    [obj.set_users(user_list) for obj in Obj_List]

    # For each object translate the data in its dataframe into an array of sets
    print('Loading user data sets')
    [obj.load_user_data_set() for obj in Obj_List]

    # create a sql table and store Jaccard distances in it.
    create_sql_table()
    print('Calculating Jaccard distances across all axes and storing via sql - {0} entries'.format(len(user_list)))
    for i in range(1, len(user_list) + 1):
        if (i%25) == 0:
            print (i)
        sql_3_axis_distances_for_one_handle(Assessments_Obj, Interests_Obj, Classes_Obj, i)
    print('Done. Data stored via sql.')
    
    
if __name__ == '__main__':
    main()

